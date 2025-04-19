import os
import tempfile
import shutil
import json
import difflib
from git import Repo
import requests
from redis import Redis
from rq import Queue

from flask import current_app
from app import db, TestRun, RepositorySubscription
from test_case_gen import ChunkedTestCaseGenerator
from models import TokenRepository,UserRepository 
from urllib.parse import quote
from io import BytesIO

# Configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CLONE_ROOT = os.environ.get('CLONE_ROOT', '/tmp/repos')
CONSISTENCY_CHECKER_URL = os.environ.get(
    'CONSISTENCY_CHECKER_URL',
    "http://localhost:5000/api/check-consistency"

)
SCENARIO_GENERATOR_URL = os.environ.get(
    'SCENARIO_GENERATOR_URL',
    'http://localhost:5001/generate-test-scenarios'
)

# Initialize Redis connection and RQ queue
redis_conn = Redis.from_url(REDIS_URL)
task_queue = Queue('regeneration', connection=redis_conn)

def clone_or_update_repo(user_id: int, repo_name: str, token: str = None):
    """
    Clone the GitHub repo if not present locally, otherwise pull the latest changes.

    Returns:
        repo (Repo): GitPython Repo object
        path (str): Local filesystem path to the repo
    """
    # user_name=UserRepository.get_by_id(user_id).username
    
    safe_name = repo_name.replace('/', '_')
    path      = os.path.join(CLONE_ROOT, str(user_id), safe_name)

    if token:
        # URL‑encode any special chars in your PAT
        tok_escaped = quote(token, safe='')
        origin      = f"https://x-access-token:{tok_escaped}@github.com/{repo_name}.git"
    else:
        origin = f"https://github.com/{repo_name}.git"

    if os.path.isdir(path):
        repo = Repo(path)
        repo.remotes.origin.pull()
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        repo = Repo.clone_from(origin, path)
    return repo, path

def generate_diff_html(user_id: int, repo_name: str) -> str:
    """
    Generate an HTML diff between existing tests in the repo and newly generated tests.

    Returns:
        str: HTML string containing diffs for each modified/new test file.
    """
    token = TokenRepository.get_for_user(user_id)
    repo, path = clone_or_update_repo(user_id, repo_name, token)

    # Read existing tests
    committed = {}
    tests_dir = os.path.join(path, 'tests')
    for root, _, files in os.walk(tests_dir):
        for fn in files:
            if fn.endswith('.py'):
                rel = os.path.relpath(os.path.join(root, fn), path)
                with open(os.path.join(root, fn), 'r') as f:
                    committed[rel] = f.read().splitlines()

    # Generate new tests in a temp directory
    tempdir = tempfile.mkdtemp()
    try:
        shutil.copytree(path, tempdir, dirs_exist_ok=True)
        generator = ChunkedTestCaseGenerator(chunk_token_limit=3000)
        generator.generate_test_cases(
            scenarios_json_path="output.json",
            codebase_url=f"https://github.com/{repo_name}",
            output_path=os.path.join(tempdir, 'all_generated_tests.json')
        )

        # Read generated tests
        generated = {}
        gen_tests = os.path.join(tempdir, 'tests')
        for root, _, files in os.walk(gen_tests):
            for fn in files:
                if fn.endswith('.py'):
                    rel = os.path.relpath(os.path.join(root, fn), tempdir)
                    with open(os.path.join(root, fn), 'r') as f:
                        generated[rel] = f.read().splitlines()

        # Build HTML diff
        diff_parts = []
        htmld = difflib.HtmlDiff(tabsize=4)
        for rel, new_lines in generated.items():
            old_lines = committed.get(rel, [])
            diff_parts.append(f"<h4>{rel}</h4>")
            diff_parts.append(
                htmld.make_file(old_lines, new_lines,
                                fromdesc='Before', todesc='After')
            )
        return '\n'.join(diff_parts)
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


def enqueue_regeneration_task(user_id: int, repo_name: str):
    """
    Enqueue a background job to regenerate tests for the given repository.
    """
    task_queue.enqueue(perform_regeneration, user_id, repo_name)


def perform_regeneration(user_id: int, repo_name: str):
    """
    Perform the full regeneration pipeline:
      1. Run consistency check
      2. Generate test scenarios
      3. Generate test cases
      4. Update TestRun status in the database
    """
    # Create a new TestRun entry
    sub = RepositorySubscription.query.filter_by(
        user_id=user_id,
        repository_url=f"https://github.com/{repo_name}"
    ).first()
    run = TestRun(subscription_id=sub.id, status='running', new_tests=0, removed_tests=0)
    db.session.add(run)
    db.session.commit()

    try:
        
        token_rec = TokenRepository.get_for_user(user_id)
        token_str = token_rec.access_token if token_rec else None

        # 2. Check if there's a document attached to the subscription
        if not sub.document or not sub.document.content:
            raise RuntimeError(f"No requirements document found for subscription {sub.id}")

        # 3. Wrap the text content in a file-like object
        doc_file = BytesIO(sub.document.content)
        doc_file.name = sub.document.filename  # e.g., "requirements.txt"
        print(f"📄 Sending file: {doc_file.name}")

        # 4. POST to the consistency checker (optional step)
        try:
            resp = requests.post(
                CONSISTENCY_CHECKER_URL,
                files={'file': (doc_file.name, doc_file, 'application/pdf')}
            )
            
            resp.raise_for_status()
            with open("consistency_report.pdf", 'wb') as f:
                f.write(resp.content)
            print("✅ Consistency detection passed")
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTPError during consistency check: {e}")
            print("Status code:", resp.status_code)
            print("Response body:", resp.text)
            raise

        # 5. Reset file pointer to the beginning
        doc_file.seek(0)

        # 6. POST to the scenario generator
        try:
            resp2 = requests.post(
                SCENARIO_GENERATOR_URL,
                files={'file': (doc_file.name, doc_file, 'text/plain')}
            )
            resp2.raise_for_status()
            scenarios = resp2.json()
            print("✅ Generated scenarios:", scenarios)
        except requests.exceptions.RequestException as e:
            print(f"❌ Error while calling scenario generator: {e}")
            raise
        # doc_file.seek(0)
        # 2. Save scenarios
        scenarios_path = os.path.abspath('output.json')
        with open(scenarios_path, 'w') as f:
            json.dump(scenarios, f, indent=2)

        # 3. Generate test cases
        generator = ChunkedTestCaseGenerator(chunk_token_limit=3000)
        output_dir = os.path.join('./tmp/test_runs', str(run.id))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'all_generated_tests.json')

        tests = generator.generate_test_cases(
            scenarios_json_path=scenarios_path,
            codebase_url=f"https://github.com/{repo_name}",
            output_path=output_path
        )
        with open(output_path, 'w') as f:
            json.dump(tests, f, indent=2)

        # 4. Update run record
        run.new_tests = len(tests)
        run.removed_tests = 0  # TODO: implement diff-based removal count
        run.status = 'success'
        run.log = ''

    except Exception as e:
        run.status = 'error'
        run.error_message = str(e)
        print("sohan")
        print(run.error_message)
        run.log = getattr(e, 'log', '')
    finally:
        db.session.commit()
        print(run.status)
        return run.id
