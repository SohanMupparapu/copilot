
import os
import secrets
import logging
from urllib.parse import urlparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, redirect, request, session, jsonify, render_template, abort,flash,url_for,send_file
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, User, GitHubToken, RepositorySubscription, TestRun,TokenRepository,SubscriptionRepository,Document
import models  # ensure models are loaded for migrations
from services import GitHubService, AuthService, SubscriptionService, TestRunService
from io import BytesIO


# ----------------------------------------------------------------------------
# Configure logging
# ----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# Load environment
# ----------------------------------------------------------------------------
load_dotenv()

# ----------------------------------------------------------------------------
# App setup
# ----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))

GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')

if not all([GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, REDIRECT_URI]):
    logger.error("Missing required environment variables for GitHub OAuth")
    raise EnvironmentError("Missing required GitHub OAuth environment variables")

parsed_uri = urlparse(REDIRECT_URI)
PUBLIC_BASE_URL = f"{parsed_uri.scheme}://{parsed_uri.netloc}"

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///app.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Additional session configuration
app.config['SESSION_TYPE'] = 'filesystem'  # Or 'redis' if you have Redis set up
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Extend session lifetime
app.config['SESSION_COOKIE_SECURE'] = False  # For HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

db.init_app(app)


# ----------------------------------------------------------------------------
# Auth Helpers
# ----------------------------------------------------------------------------
def get_current_user_id():
    user_id = session.get('user_id')
    if not user_id:
        abort(401, description="User not authenticated")
    return user_id

# ----------------------------------------------------------------------------
# OAuth Routes
# ----------------------------------------------------------------------------
@app.route('/connect-github')
def connect_github():
    # Generate a secure random state token
    state = secrets.token_hex(32)  # Increased from 16 to 32 for more security
    
    # Store state in session
    session.clear()  # Clear any existing session data
    session['oauth_state'] = state
    session['oauth_state_time'] = datetime.utcnow().timestamp()
    session.permanent = True  # Make the session last longer
    # print(session)
    # Log the session creation (for debugging)
    logger.info(f"Creating new OAuth session with state={state}")
    
    # Generate the authorization URL
    url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=repo"
        f"&state={state}"
    )
    
    # Force a session save before redirecting
    session.modified = True
    
    return redirect(url)

@app.route('/github/callback')
def github_callback():
    # Get the state from the request and session
    callback_state = request.args.get('state')
    session_state = session.get('oauth_state')
    # print("callback")
    # print(session_state)
    # Log the states for debugging
    logger.info(f"GitHub callback received. Callback state={callback_state}, Session state={session_state}")
    
    # Check if the state matches
    if not callback_state or callback_state != session_state:
        logger.warning(f"State mismatch: callback={callback_state}, session={session_state}")
        return render_template('error.html', 
                              message="Authentication failed: State mismatch. Please try again."), 403
    
    # Continue with the OAuth flow
    try:
        code = request.args.get('code')
        user = AuthService.authenticate_user(code)
        session['user_id'] = user.id
        
        # Force a session save
        session.modified = True
        
        return redirect('/select-repository')
    
    except Exception as e:
        logger.exception(f"Error in GitHub callback: {str(e)}")
        return render_template('error.html', 
                              message="Failed to authenticate with GitHub: " + str(e)), 500
# ----------------------------------------------------------------------------
# Repository Subscription Routes
# ----------------------------------------------------------------------------
@app.route('/select-repository')
def select_repository():
    try:
        user_id = get_current_user_id()
        token_record = TokenRepository.get_for_user(user_id)
        
        if not token_record:
            return redirect('/connect-github')
        
        repositories = GitHubService.get_user_repositories(token_record.access_token)
        return render_template('select_repository.html', repositories=repositories)
    
    except Exception as e:
        logger.exception(f"Error in select_repository: {str(e)}")
        return render_template('error.html', message="Failed to retrieve repositories"), 500


@app.route('/subscribe-repo', methods=['POST'])
def subscribe_repo():
    try:
        repo_full = request.form.get('repository_name')
        if not repo_full:
            return jsonify(error="Repository name required"), 400
        
        user_id = get_current_user_id()
        SubscriptionService.create_subscription(user_id, repo_full)
        return redirect('/dashboard')
    
    except Exception as e:
        logger.exception(f"Error in subscribe_repo: {str(e)}")
        return jsonify(error=str(e)), 500




@app.route('/api/regenerate', methods=['POST'])
def api_regenerate():
    try:
        repo = request.form['repo']
        user_id = get_current_user_id()
        
        test_run = TestRunService.enqueue_regeneration_task(
            user_id, f"https://github.com/{repo}"
        )
        
        return jsonify(started=True, test_run_id=test_run.id if test_run else None)
    
    except Exception as e:
        logger.exception(f"Error in api_regenerate: {str(e)}")
        return jsonify(error=str(e)), 500
@app.route('/dashboard')
def dashboard():
    user_id = get_current_user_id()
    subs = SubscriptionRepository.get_user_subscriptions(user_id)

    for sub in subs:
        if sub.new_tests_available:
            flash(f"✅ New test cases generated for {sub.repository_url}", 'info')
            sub.new_tests_available = False
            db.session.add(sub)

    # flush all flag‑clears in one go
    db.session.commit()

    return render_template('dashboard.html', subscriptions=subs)


@app.route('/api/add-repo', methods=['POST'])
# @login_required
def add_repo():
    user_id = get_current_user_id()
    repo = request.form['repo_url']
    sub = SubscriptionRepository.create(user_id, repo)
    if not sub:
        flash('You have already subscribed to this repository.', 'warning')
    else:
        flash(f'Successfully added {repo}.', 'success')
    return redirect(url_for('repos.dashboard'))

@app.route('/api/delete-repo', methods=['POST'])
def delete_repo():
    repo = request.form.get('repo')
    user_id = get_current_user_id()
    print(user_id)
    sub = RepositorySubscription.query.filter_by(
        user_id=user_id,
        repository_url=repo
    ).first()
    if not sub:
        return jsonify({'error': 'Subscription not found.'}), 404

    db.session.delete(sub)
    db.session.commit()
    return jsonify({'success': True})

# @app.route('/repo/<int:sub_id>')
# def repo_detail(sub_id):
#     sub = RepositorySubscription.query.get_or_404(sub_id)
#     user_id = get_current_user_id()
#     if sub.user_id != user_id:
#         abort(403)

#     return render_template('repo_detail.html', sub=sub)

@app.route('/repo/<int:sub_id>')
def repo_detail(sub_id):
    sub = RepositorySubscription.query.get_or_404(sub_id)
    user_id = get_current_user_id()
    if sub.user_id != user_id:
        abort(403)

    if sub.new_tests_available:
        flash("✅ New test cases have been generated for this repository!", 'info')
        sub.new_tests_available = False
        db.session.commit()
    
    run_id = session.pop('last_generated_run_id', None)
    repo_name = session.pop('last_generated_repo', None)
    return render_template("repo_detail.html", sub=sub, run_id=run_id, repo_name=repo_name)
    # return render_template('repo_detail.html', sub=sub)


@app.route('/repo/<int:sub_id>/upload-document', methods=['POST'])
def upload_document(sub_id):
    from helpers import perform_regeneration
    sub = RepositorySubscription.query.get_or_404(sub_id)
    user_id = get_current_user_id()
    if sub.user_id != user_id:
        abort(403)

    file = request.files.get('document')
    if not file:
        flash('No file selected.', 'danger')
        return redirect(url_for('repo_detail', sub_id=sub_id))

    data = file.read()
    if sub.document:
        sub.document.filename = file.filename
        sub.document.content  = data
    else:
        doc = Document(
            subscription_id=sub.id,
            filename=file.filename,
            content=data
        )
        db.session.add(doc)

    db.session.commit()
    flash('Document saved. Generating tests…', 'info')

    # --- synchronous generation! ---
    # extract “owner/repo” from your full URL
    repo_name = sub.repository_url.split('github.com/')[-1]
    run_id    = perform_regeneration(user_id, repo_name)
    sub.last_run_id=run_id
    print(f"run_id: {run_id}")

    # build the path exactly as you did in perform_regeneration
    file_path = os.path.join('/tmp/test_runs', str(run_id), 'all_generated_tests.json')
    session['last_generated_run_id'] = run_id
    session['last_generated_repo'] = repo_name.replace('/', '_')
    # return redirect(url_for('repo_detail', sub_id=sub_id))

    if not os.path.exists(file_path):
        flash('Test generation failed or file not found.', 'danger')
        return redirect(url_for('repo_detail', sub_id=sub_id))

    # stream it back right away
    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"{repo_name.replace('/', '_')}_tests_{run_id}.json"
    )


@app.route('/download-tests/<int:run_id>')
def download_tests(run_id):
    run = TestRun.query.get_or_404(run_id)
    print(run)
    file_path = os.path.join('./tmp/test_runs', str(run_id), 'all_generated_tests.json')
    # file_path=
    print(file_path)
    if not os.path.exists(file_path):
        abort(404, description="Generated test file not found.")

    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"generated_tests_run_{run_id}.json"
    )

# ----------------------------------------------------------------------------
# Error Handlers
# ----------------------------------------------------------------------------
@app.errorhandler(401)
def unauthorized(error):
    return redirect('/connect-github')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', message="Page not found"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('error.html', message="Internal server error"), 500

# ----------------------------------------------------------------------------
# App initialization
# ----------------------------------------------------------------------------
def poll_github_events():
    logger.debug("Polling GitHub events...")
    with app.app_context():
        active = SubscriptionRepository.get_active_subscriptions()
        for sub in active:
            token_rec = TokenRepository.get_for_user(sub.user_id)
            if not token_rec:
                logger.warning(f"No token for user {sub.user_id}")
                continue

            events = GitHubService.get_repository_events(token_rec.access_token, sub.repository_url)
            if not events:
                continue

            # process_repository_events returns a list of new events
            new_events = SubscriptionService.process_repository_events(sub, events)
            if not new_events:
                continue

            # For each new event, enqueue regeneration and mark the flag
            for _ in new_events:
                test_run = TestRunService.enqueue_regeneration_task(sub.user_id, sub.repository_url)
                sub.last_run_id = test_run.id
                sub.new_tests_available = True

            db.session.add(sub)

        # Commit once per batch
        db.session.commit()


def initialize_app():
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        
        # Start background scheduler if not in testing mode
        if not app.config.get('TESTING'):
            scheduler = BackgroundScheduler()
            scheduler.add_job(poll_github_events, 'interval', seconds=60)
            scheduler.start()
            
            # Register shutdown handler
            import atexit
            atexit.register(lambda: scheduler.shutdown())

# ----------------------------------------------------------------------------
# App entrypoint
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    initialize_app()
    app.run(debug=True, port=8000)
else:
    # For WSGI servers
    initialize_app()
# from app import db
# db.drop_all()
# db.create_all()
