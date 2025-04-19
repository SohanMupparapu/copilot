# 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
# import os
# import json
# from groq import Groq
# 
# class TestCaseGenerator:
#     """
#     A reusable class for generating test cases from a GroqCloud LLM.
#     Rename this class and update MODEL_NAME to target different models.
#     """

#     # ======== Configuration ========
#     MODEL_NAME = "distil-whisper-large-v3-en"   # <-- change this to your target model
#     API_KEY_ENV = "GROQ_API_KEY"             # <-- change if you use a different env var

#     # ======== Initialization ========
#     def __init__(self, api_key: str = None):
#         """
#         Initialize the Groq client.
#         If api_key is None, will read from environment variable.
#         """
#         self.api_key="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"
#         self.client = Groq(api_key=self.api_key)

#     # ======== Prompt Builder ========
#     def _build_prompt(self, scenarios: dict, codebase_url: str) -> str:
#         """
#         Build the instruction prompt for the LLM.
#         """
#         prompt = (
#             "You are an automated test case generator. "
#             "Based on the following test scenarios and codebase, "
#             "produce a comprehensive set of unit test cases in JSON format.\n\n"
#             f"Test Scenarios:\n{json.dumps(scenarios, indent=2)}\n\n"
#             f"Codebase URL: {codebase_url}\n\n"
#             "Return only valid JSON with an array of test case definitions."
#         )
#         return prompt

#     # ======== Core Method ========
#     def generate_test_cases(self,
#                             scenarios_json_path: str,
#                             codebase_url: str,
#                             output_path: str = None) -> dict:
#         """
#         Generate test cases via the LLM.

#         :param scenarios_json_path: Path to JSON file containing test scenarios.
#         :param codebase_url: URL of the GitHub repo or codebase.
#         :param output_path: If provided, will write the LLM response JSON here.
#         :return: Parsed JSON from the LLM.
#         """
#         # 1. Load scenarios
#         with open(scenarios_json_path, 'r') as f:
#             scenarios = json.load(f)

#         # 2. Build prompt
#         prompt = self._build_prompt(scenarios, codebase_url)

#         # 3. Call the LLM
#         response = self.client.chat.completions.create(
#             model=self.MODEL_NAME,
#             messages=[
#                 {"role": "system", "content": "You are a helpful assistant."},
#                 {"role": "user",   "content": prompt}
#             ]
#         )

#         # 4. Extract content
#         content = response.choices[0].message.content

#         # 5. Parse JSON
#         try:
#             test_cases = json.loads(content)
#         except json.JSONDecodeError as e:
#             raise RuntimeError(f"Failed to parse LLM response as JSON: {e}\nRaw content:\n{content}")

#         # 6. Optionally write to file
#         if output_path:
#             with open(output_path, 'w') as out:
#                 json.dump(test_cases, out, indent=2)

#         return test_cases

# if __name__ == "__main__":
#     # 1. Export your key: export GROQ_API_KEY="your-key-here"
#     gen = TestCaseGenerator()

#     # 2. Provide your scenarios JSON and GitHub URL
#     scenarios_path = "output.json"
#     repo_url = "https://github.com/kryptonblade/banking_dummy.git"

#     # 3. Generate and save test cases
#     test_cases = gen.generate_test_cases(
#         scenarios_json_path=scenarios_path,
#         codebase_url=repo_url,
#         output_path="generated_tests.json"
#     )

#     print(f"Generated {len(test_cases)} test cases.")



# groq_clients.py
import os
import json
from groq import Groq, APIStatusError, BadRequestError
import tiktoken


import re

def extract_json_block(text: str) -> str:
    m = re.search(r"(\[.*\])", text, re.DOTALL)
    if not m:
        raise RuntimeError(f"No JSON array could be extracted:\n{text}")
    raw = m.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON:\n{raw}\nError was: {e}")


class TestCaseGenerator:
    """
    Single-shot test-case generator using GroqCloud LLM.
    """
    MODEL_NAME = "llama-3.3-70b-versatile"
    API_KEY_ENV = "GROQ_API_KEY"

    def __init__(self, api_key: str = None):
        self.api_key = "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"
        self.client = Groq(api_key=self.api_key)

    def _build_prompt(self, scenarios: list, codebase_url: str) -> str:
        """
        Build the LLM prompt from a list of scenario dicts.
        Each scenario dict contains keys: id, requirement, scenarios (text).
        """
        prompt = (
            "You are an automated test case generator. "
            "Based on the following requirements and test scenarios for a codebase, "
            "produce a comprehensive set of unit test cases in JSON format.\n\n"
            f"Requirements & Scenarios:\n{json.dumps(scenarios, indent=2)}\n\n"
            f"Codebase URL: {codebase_url}\n\n"
            "Return only valid JSON with an array of test case definitions."
        )
        return prompt

    def _extract_scenarios(self, raw: dict) -> list:
        """
        Transform raw input JSON into a list of scenario objects.
        Expects raw like:
        {
        "requirements": [
            {"id": "R1", "text": "..."},
            ...
        ]
        }
        """
        if 'requirements' not in raw or not isinstance(raw['requirements'], list):
            raise ValueError("Input JSON must have a 'requirements' list")
        
        scenarios = []
        for entry in raw['requirements']:
            scenarios.append({
                'id': entry.get('id', ''),
                'requirement': entry.get('text', ''),
                'scenarios': ''  # Placeholder, assuming generation is done later
            })
        return scenarios

    def generate_test_cases(self,
                            scenarios_json_path: str,
                            codebase_url: str,
                            output_path: str = None) -> list:
        # 1. Load raw JSON and extract scenarios list
        with open(scenarios_json_path, 'r') as f:
            raw = json.load(f)
        scenarios = self._extract_scenarios(raw)

        # 2. Build and send prompt
        prompt = self._build_prompt(scenarios, codebase_url)
        response = self.client.chat.completions.create(
            model=self.MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",   "content": prompt}
            ]
        )

        # 3. Parse LLM response
        content = response.choices[0].message.content
        try:
            test_cases = extract_json_block(content)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse LLM response as JSON: {e}\nRaw content:\n{content}")

        # 4. Optionally write to file
        if output_path:
            with open(output_path, 'w') as out:
                json.dump(test_cases, out, indent=2)
        return test_cases


class ChunkedTestCaseGenerator(TestCaseGenerator):
    """
    Splits input scenarios into token-based chunks, invokes LLM per chunk,
    and aggregates all test cases into a single list.
    """
    def __init__(self,
                 api_key: str = None,
                 chunk_token_limit: int = 3000,
                 encoding_name: str = "gpt2"):
        super().__init__(api_key)
        self.chunk_token_limit = chunk_token_limit
        self.encoding = tiktoken.get_encoding(encoding_name)

    def _count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def _chunk_scenarios(self, scenarios: list) -> list:
        chunks, current = [], []
        for scen in scenarios:
            entry = json.dumps(scen)
            if self._count_tokens(entry) > self.chunk_token_limit:
                raise ValueError(
                    f"Single scenario '{scen.get('id')}' exceeds token limit"
                )
            combined = json.dumps(current + [scen])
            if self._count_tokens(combined) <= self.chunk_token_limit:
                current.append(scen)
            else:
                chunks.append(current)
                current = [scen]
        if current:
            chunks.append(current)
        return chunks

    def generate_test_cases(self,
                        scenarios_json_path: str,
                        codebase_url: str,
                        output_path: str = None) -> list:
        """
        Generate test cases by processing scenarios in chunks.
        """
        # Load and extract scenarios list
        with open(scenarios_json_path, 'r') as f:
            raw = json.load(f)
        scenarios = self._extract_scenarios(raw)

        # Break into chunks
        chunks = self._chunk_scenarios(scenarios)
        all_tests = []
        
        # Progress tracking
        total_chunks = len(chunks)
        print(f"Processing {total_chunks} chunks...")

        # Call LLM on each chunk
        for idx, chunk in enumerate(chunks, start=1):
            print(f"Processing chunk {idx}/{total_chunks}...")
            prompt = self._build_prompt(chunk, codebase_url)
            
            try:
                response = self.client.chat.completions.create(
                    model=self.MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are a test case generator. Output valid JSON test cases."},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                content = response.choices[0].message.content
                
                # Extract JSON from markdown if necessary
                cleaned_content = self._extract_json_from_response(content)
                
                if not cleaned_content.strip():
                    print(f"Warning: Empty response for chunk {idx}")
                    continue
                    
                try:
                    tests = json.loads(cleaned_content)
                    
                    # Validate the structure of returned tests
                    if not isinstance(tests, list):
                        print(f"Warning: Expected list of tests but got {type(tests)} for chunk {idx}")
                        if isinstance(tests, dict):
                            # Handle case where a single test is returned as dict
                            tests = [tests]
                        else:
                            continue
                            
                    all_tests.extend(tests)
                                        # print(f"JSON parsing error in chunk {idx}:")
                    print(f"Response content: {content[:200]}...")  # Print first 200 chars
                    print(f"Cleaned content: {cleaned_content[:200]}...")  # Print cleaned content for debugging
                    # raise RuntimeError(
                    #     f"Failed parsing chunk {idx} JSON: {e}"
                    # )

                    print(f"Added {len(tests)} tests from chunk {idx}")
                    
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error in chunk {idx}:")
                    print(f"Response content: {content[:200]}...")  # Print first 200 chars
                    print(f"Cleaned content: {cleaned_content[:200]}...")  # Print cleaned content for debugging
                    raise RuntimeError(
                        f"Failed parsing chunk {idx} JSON: {e}"
                    )
                
            except APIStatusError as e:
                if e.status_code == 413:
                    raise RuntimeError(
                        f"Chunk {idx} too large: reduce chunk_token_limit"
                    ) from e
                print(f"API error in chunk {idx}: {e}")
                raise
            except Exception as e:
                print(f"Unexpected error processing chunk {idx}: {e}")
                raise

        print(f"Successfully generated {len(all_tests)} test cases in total")
        
        # Write aggregated output
        if output_path:
            with open(output_path, 'w') as out:
                json.dump(all_tests, out, indent=2)
                
        return all_tests

    def _extract_json_from_response(self, content: str) -> str:
        """
        Extract JSON from a potentially markdown-formatted response.
        
        Args:
            content: Raw response from the model
            
        Returns:
            Cleaned JSON string
        """
        # First, check if we're dealing with markdown code blocks
        if "```" in content:
            # Try to extract content between code block markers
            import re
            
            # Pattern to match content between triple backticks
            # This pattern carefully captures everything between the opening and closing markers
            pattern = r"```(?:json)?[\s\n]+([\s\S]+?)[\s\n]+```"
            
            match = re.search(pattern, content)
            if match:
                # Extract the content from group 1 (what's between the backticks)
                extracted = match.group(1).strip()
                print("sohan")
                return extracted
                
        # If the content doesn't contain code blocks or extraction failed,
        # return the original content which might already be plain JSON
        return content.strip()

if __name__ == "__main__":
    # Example usage
    generator = ChunkedTestCaseGenerator(chunk_token_limit=3000)
    tests = generator.generate_test_cases(
        scenarios_json_path="output.json",
        codebase_url="https://github.com/kryptonblade/banking_dummy.git",
        output_path="all_generated_tests.json"
    )
    print(f"Total test cases generated: {len(tests)}")