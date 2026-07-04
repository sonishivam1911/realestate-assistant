from langchain_groq import ChatGroq
from output_parser import ActionParser
import json
import re
from prompts.emailReflectionPrompt import get_email_reflection_prompt_template


class EmailReflectionAgent:
    """
    Reviews and improves generated emails for professional quality
    Acts as an expert English language orator and writer
    Iteratively improves until score reaches 8/10 or higher
    Uses Groq for fast LLM inference
    """
    
    def __init__(self, model: str = "llama-3.1-8b-instant"):
        self.llm = ChatGroq(
            model=model,
            temperature=0.7,
            max_tokens=2000
        )
        self.parser = ActionParser(use_json_repair=True)
        self.max_iterations = 2  # Maximum 2 improvement iterations
    
    def reflect_and_improve_email(self, email_data: dict, state: dict) -> dict:
        """
        Review and improve email until quality score reaches 8/10
        
        Args:
            email_data: Generated email with subject and body
            state: Workflow state for context
        
        Returns:
            Dict with improved email and quality metrics
        """
        
        print(f"\n{'#'*80}")
        print(f"# EMAIL REFLECTION & QUALITY ASSURANCE")
        print(f"{'#'*80}")
        
        current_email = email_data.copy()
        current_score = 0
        iteration = 0
        
        while current_score < 8 and iteration < self.max_iterations:
            iteration += 1
            print(f"\n🔍 Reflection Iteration {iteration}/{self.max_iterations}")
            
            try:
                # Prepare reflection variables
                valuation_report = state.get('valuation_report', {})
                preprocessed_data = state.get('preprocessed_data', {})
                target_property = state.get('target_property', {})
                
                template_vars = {
                    "current_subject": current_email.get('subject', ''),
                    "current_body": current_email.get('body', ''),
                    "target_property": target_property.get('address', 'Unknown'),
                    "estimated_value": valuation_report.get('analysis_summary', {}).get('estimated_value', '$0'),
                    "comparable_count": len(preprocessed_data.get('filtered_sold_homes', [])),
                    "confidence_level": valuation_report.get('analysis_summary', {}).get('confidence_level', 'Unknown')
                }
                
                # Get reflection prompt
                prompt = get_email_reflection_prompt_template()
                formatted_prompt = prompt.format(**template_vars)
                
                print(f"   🤖 Analyzing email quality...")
                response = self.llm.invoke(formatted_prompt)
                response_text = response.content
                
                print(f"   📝 Raw response length: {len(response_text)}")
                
                # Parse text response instead of JSON
                reflection_result = self._parse_reflection_response(response_text)
                current_score = reflection_result['final_score']
                
                print(f"   📊 Score: {current_score}/10")
                
                if reflection_result['improvement_needed']:
                    print(f"   ✏️  Improvements being applied...")
                    current_email['subject'] = reflection_result.get('improved_subject', current_email['subject'])
                    current_email['body'] = reflection_result.get('improved_body', current_email['body'])
                else:
                    print(f"   ✅ Email quality is sufficient (score: {current_score}/10)")
                    break
            
            except Exception as e:
                print(f"   ❌ Reflection iteration failed: {str(e)}")
                print(f"   ⚠️  Returning email with current quality")
                # Use fallback score
                current_score = 5
                break
        
        print(f"\n{'#'*80}")
        print(f"✅ REFLECTION COMPLETE")
        print(f"{'#'*80}")
        print(f"Final Score: {current_score}/10")
        print(f"Iterations: {iteration}")
        print(f"Status: {'Ready to send ✓' if current_score >= 8 else 'Quality threshold not met'}")
        
        # Return only subject, body, and quality metrics
        return {
            "subject": current_email['subject'],
            "body": current_email['body'],
            "final_quality_score": current_score,
            "reflection_iterations": iteration,
            "ready_to_send": current_score >= 8
        }
    
    def _parse_reflection_response(self, response_text: str) -> dict:
        """
        Parse simplified text-format reflection response from LLM
        
        Args:
            response_text: Plain text response with score and improved email
        
        Returns:
            Dict with parsed reflection results
        """
        
        result = {
            'final_score': 0,
            'issues': [],
            'improvement_needed': False,
            'improved_subject': '',
            'improved_body': ''
        }
        
        lines = response_text.split('\n')
        
        # Extract score
        for line in lines:
            if 'score:' in line.lower() and '/' in line:
                match = re.search(r'(\d+)\s*/\s*10', line)
                if match:
                    result['final_score'] = int(match.group(1))
                    break
        
        # If score >= 8, no improvements needed
        if result['final_score'] >= 8:
            result['improvement_needed'] = False
            return result
        
        # Extract improved email if score < 8
        result['improvement_needed'] = True
        improved_started = False
        subject_found = False
        body_lines = []
        
        for i, line in enumerate(lines):
            # Look for improved email section
            if '🔧 improved email:' in line.lower() or 'improved email:' in line.lower():
                improved_started = True
                continue
            
            if improved_started:
                # Extract subject
                if 'subject:' in line.lower() and not subject_found:
                    result['improved_subject'] = line.replace('Subject:', '').replace('subject:', '').strip()
                    subject_found = True
                elif subject_found and line.strip():
                    # This is body content
                    body_lines.append(line)
        
        result['improved_body'] = '\n'.join(body_lines).strip() if body_lines else ''
        
        # If still no score extracted, default to 7
        if result['final_score'] == 0:
            result['final_score'] = 7
            result['improvement_needed'] = True
        
        return result
    
    def _parse_reflection_fallback(self, response_text: str) -> dict:
        """
        Fallback parser for reflection responses
        """
        result = {
            'final_score': 7,  # Default to 7/10 if parsing fails
            'score_breakdown': {
                'professionalism': 2,
                'clarity': 1,
                'completeness': 1,
                'coherence': 1,
                'effectiveness': 2
            },
            'issues': [],
            'assessment': 'Email quality assessed',
            'improvement_needed': False,
            'improved_subject': '',
            'improved_body': ''
        }
        return result

