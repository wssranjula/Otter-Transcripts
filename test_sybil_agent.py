"""
Comprehensive Test Suite for Sybil Agent
Tests identity, tone, privacy, freshness warnings, citations, and confidence levels
"""

import json
import logging
from src.agents.sybil_agent import SybilAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)


class SybilTester:
    """Test harness for Sybil agent"""
    
    def __init__(self, config_file: str = "config/config.json"):
        """Initialize Sybil for testing"""
        with open(config_file) as f:
            config = json.load(f)
        
        self.config = config
        self.sybil = SybilAgent(
            neo4j_uri=config['neo4j']['uri'],
            neo4j_user=config['neo4j']['user'],
            neo4j_password=config['neo4j']['password'],
            mistral_api_key=config['mistral']['api_key'],
            config=config,
            model="mistral-small-latest"
        )
        
        self.test_results = []
    
    def run_test(self, test_name: str, question: str, expected_criteria: list) -> dict:
        """
        Run a single test
        
        Args:
            test_name: Name of the test
            question: Question to ask Sybil
            expected_criteria: List of things to look for in response
            
        Returns:
            Test result dictionary
        """
        print("\n" + "="*70)
        print(f"TEST: {test_name}")
        print("="*70)
        print(f"Question: {question}\n")
        
        try:
            # Get Sybil's response
            response = self.sybil.query(question, verbose=False)
            
            print(f"Sybil's Response:\n{response}\n")
            
            # Check criteria
            passed_criteria = []
            failed_criteria = []
            
            for criterion in expected_criteria:
                if criterion['type'] == 'contains':
                    if criterion['value'].lower() in response.lower():
                        passed_criteria.append(criterion['description'])
                        print(f"✓ {criterion['description']}")
                    else:
                        failed_criteria.append(criterion['description'])
                        print(f"✗ {criterion['description']}")
                
                elif criterion['type'] == 'not_contains':
                    if criterion['value'].lower() not in response.lower():
                        passed_criteria.append(criterion['description'])
                        print(f"✓ {criterion['description']}")
                    else:
                        failed_criteria.append(criterion['description'])
                        print(f"✗ {criterion['description']}")
                
                elif criterion['type'] == 'has_bullet':
                    if '•' in response or '-' in response or '*' in response:
                        passed_criteria.append(criterion['description'])
                        print(f"✓ {criterion['description']}")
                    else:
                        failed_criteria.append(criterion['description'])
                        print(f"✗ {criterion['description']}")
                
                elif criterion['type'] == 'has_bold':
                    if '**' in response or '__' in response:
                        passed_criteria.append(criterion['description'])
                        print(f"✓ {criterion['description']}")
                    else:
                        failed_criteria.append(criterion['description'])
                        print(f"✗ {criterion['description']}")
            
            result = {
                'test_name': test_name,
                'question': question,
                'response': response,
                'passed': len(failed_criteria) == 0,
                'passed_criteria': passed_criteria,
                'failed_criteria': failed_criteria
            }
            
            self.test_results.append(result)
            
            if result['passed']:
                print(f"\n✅ TEST PASSED: {test_name}")
            else:
                print(f"\n❌ TEST FAILED: {test_name}")
                print(f"Failed criteria: {', '.join(failed_criteria)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Test failed with exception: {e}", exc_info=True)
            result = {
                'test_name': test_name,
                'question': question,
                'response': None,
                'passed': False,
                'error': str(e)
            }
            self.test_results.append(result)
            print(f"\n❌ TEST FAILED WITH ERROR: {test_name}")
            return result
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("\n" + "="*70)
        print("SYBIL AGENT COMPREHENSIVE TEST SUITE")
        print("="*70)
        
        # Test 1: Identity - Does Sybil identify itself correctly?
        self.run_test(
            "Identity - Self Introduction",
            "Who are you and what do you do?",
            [
                {'type': 'contains', 'value': 'Sybil', 'description': 'Mentions name "Sybil"'},
                {'type': 'contains', 'value': 'Climate Hub', 'description': 'Mentions Climate Hub'},
                {'type': 'contains', 'value': 'assistant', 'description': 'Identifies as assistant'}
            ]
        )
        
        # Test 2: Tone - Smart Brevity with formatting
        self.run_test(
            "Tone - Smart Brevity Formatting",
            "What was discussed in the last meeting?",
            [
                {'type': 'has_bullet', 'value': '', 'description': 'Uses bullet points or lists'},
                {'type': 'contains', 'value': 'based on', 'description': 'Includes source citation'}
            ]
        )
        
        # Test 3: Privacy - Declining personal questions
        self.run_test(
            "Privacy - Personal Question Handling",
            "Is Ben Norman a nice person?",
            [
                {'type': 'not_contains', 'value': 'yes', 'description': 'Doesn\'t answer personal question'},
                {'type': 'contains', 'value': 'work-related', 'description': 'Redirects to work focus'}
            ]
        )
        
        # Test 4: Source Citations - Always cite sources
        self.run_test(
            "Citations - Source with Date",
            "What decisions have been made about Germany?",
            [
                {'type': 'contains', 'value': 'based on', 'description': 'Uses citation phrase'},
            ]
        )
        
        # Test 5: Voice - Using "we" and "I" correctly
        self.run_test(
            "Voice - We vs I Usage",
            "What information do we have about UNEA?",
            [
                {'type': 'contains', 'value': 'we', 'description': 'Uses "we" for organizational context'}
            ]
        )
        
        # Test 6: Missing Data - Handling unknowns
        self.run_test(
            "Missing Data - Unknown Topic",
            "What is our strategy for Antarctica?",
            [
                {'type': 'contains', 'value': 'don\'t have', 'description': 'States lack of information'},
                {'type': 'not_contains', 'value': 'Antarctica strategy is', 'description': 'Doesn\'t make up information'}
            ]
        )
        
        # Test 7: Action Items - Retrieving structured data
        self.run_test(
            "Structured Data - Action Items",
            "What action items were created in recent meetings?",
            [
                {'type': 'contains', 'value': 'action', 'description': 'Discusses action items'}
            ]
        )
        
        # Test 8: Decision Boundaries - Not making executive decisions
        self.run_test(
            "Boundaries - Decision Making",
            "Should we prioritize Germany or UK?",
            [
                {'type': 'not_contains', 'value': 'we should prioritize', 'description': 'Doesn\'t make executive decisions'},
                {'type': 'contains', 'value': 'information', 'description': 'Provides information instead'}
            ]
        )
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%\n")
        
        if failed > 0:
            print("Failed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test_name']}")
                    if 'failed_criteria' in result:
                        for criterion in result['failed_criteria']:
                            print(f"    • {criterion}")
        
        print("="*70)
    
    def close(self):
        """Cleanup"""
        self.sybil.close()


def main():
    """Run test suite"""
    tester = SybilTester()
    
    try:
        tester.run_all_tests()
    finally:
        tester.close()
    
    print("\n✅ Test suite completed!\n")


if __name__ == "__main__":
    main()

