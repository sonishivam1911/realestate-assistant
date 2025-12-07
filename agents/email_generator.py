from langchain_groq import ChatGroq
from output_parser import ActionParser
import json
from prompts.emailGenerationPrompt import get_email_generation_prompt_template, EMAIL_GENERATION_PROMPT


class EmailGeneratorAgent:
    """
    Generates professional client emails explaining property valuations
    Uses Groq for fast LLM inference
    
    Email Structure:
    1. Introduction - Greeting & purpose
    2. Valuation Summary - Main finding
    3. Corroborating Properties - Selected properties with links & analysis
    4. Market Analysis - Broader context
    5. Closing Remarks - Call to action
    """
    
    def __init__(self, model: str = "llama-3.1-8b-instant"):
        self.llm = ChatGroq(
            model=model,
            temperature=0.7,
            max_tokens=2500
        )
        self.parser = ActionParser(use_json_repair=True)
    
    def generate_email(self, state: dict, recipient_name: str) -> dict:
        """
        Generate professional email from valuation analysis with selected properties
        
        Args:
            state: Workflow state containing valuation and property data
            recipient_name: Name of email recipient (client name)
        
        Returns:
            Dict with email subject and body
        """
        
        print(f"\n{'#'*80}")
        print(f"# EMAIL GENERATION (WITH SELECTED PROPERTIES)")
        print(f"{'#'*80}")
        print(f"📧 Generating email for: {recipient_name}")
        
        try:
            # Check if this is a feedback-based regeneration
            user_feedback = state.get('user_feedback')
            previous_email = state.get('previous_email')
            feedback_history = state.get('feedback_history', [])
            
            if user_feedback and previous_email:
                print(f"🔄 Regenerating email with user feedback...")
                return self._generate_email_with_feedback(state, recipient_name, user_feedback, previous_email, feedback_history)
            else:
                print(f"📝 Generating initial email...")
                return self._generate_initial_email(state, recipient_name)
        
        except Exception as e:
            print(f"❌ Email generation failed: {str(e)}")
            raise
    
    def _generate_initial_email(self, state: dict, recipient_name: str) -> dict:
        """Generate initial email using the concise template format"""
        
        # Extract required data from state
        valuation_report = state.get('valuation_report', {})
        preprocessed_data = state.get('preprocessed_data', {})
        target_property = state.get('target_property', {})
        selected_properties = state.get('selected_properties', [])  # ✅ User selected properties
        
        print(f"📊 Selected properties for email: {len(selected_properties)}")
        
        try:
            # Prepare comparable properties for the prompt
            comparable_properties = self._format_comparables_for_prompt(selected_properties)
            
            # Prepare valuation summary for prompt
            analysis_summary = valuation_report.get('analysis_summary', {})
            valuation_summary = f"""
Estimated Value: {analysis_summary.get('estimated_value', 'N/A')}
Asking Price: ${target_property.get('asking_price', 0):,}
Verdict: {analysis_summary.get('verdict', 'FAIRLY_PRICED').upper()}
Variance: {analysis_summary.get('variance_percent', '0%')}
Rationale: {analysis_summary.get('why_this_price', 'Based on market analysis')}
"""
            
            # Get prompt template and format it
            from prompts.emailGenerationPrompt import get_email_generation_prompt_template
            prompt = get_email_generation_prompt_template()
            
            # Create template variables
            template_vars = {
                'target_property_details': f"{target_property.get('address', 'Unknown')} - {target_property.get('bedrooms', 0)} bed, {target_property.get('bathrooms', 0)} bath, {target_property.get('sqft', 0)} sqft - Asking: ${target_property.get('asking_price', 0):,}",
                'valuation_summary': valuation_summary.strip(),
                'comparable_properties': comparable_properties
            }
            
            # Format the prompt
            formatted_prompt = prompt.format(**template_vars)
            
            # Get LLM response
            response = self.llm.invoke(formatted_prompt)
            response_text = response.content.strip()
            
            # Parse the response to extract subject and body
            if "Subject:" in response_text:
                lines = response_text.split('\n')
                subject_line = ""
                body_lines = []
                found_subject = False
                
                for line in lines:
                    if line.strip().lower().startswith('subject:'):
                        subject_line = line.replace('Subject:', '').replace('subject:', '').strip()
                        found_subject = True
                    elif found_subject and line.strip():
                        body_lines.append(line)
                
                subject = subject_line if subject_line else f"Property Valuation - {target_property.get('address', '')}"
                body = '\n'.join(body_lines).strip()
            else:
                # Fallback: use first line as subject, rest as body
                lines = response_text.split('\n')
                subject = lines[0].strip() if lines else "Property Valuation Update"
                body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else response_text
            
            print(f"✅ Email generated successfully")
            print(f"   Subject: {subject}")
            print(f"   Body length: {len(body)}")
            
            return {
                "subject": subject,
                "body": body
            }
            
        except Exception as e:
            print(f"❌ Error generating concise email: {str(e)}")
            # Fallback to legacy format
            return self._generate_legacy_email(state, recipient_name)
    
    def _generate_legacy_email(self, state: dict, recipient_name: str) -> dict:
        """Legacy email generation method using the structured format"""
        
        # Extract required data from state
        valuation_report = state.get('valuation_report', {})
        preprocessed_data = state.get('preprocessed_data', {})
        target_property = state.get('target_property', {})
        selected_properties = state.get('selected_properties', [])
        
        # Build email sections using legacy methods
        introduction = self._build_introduction(recipient_name, target_property)
        valuation_summary = self._build_valuation_summary(valuation_report, target_property)
        corroborating_section = self._build_corroborating_properties_section(selected_properties)
        market_analysis = self._build_market_analysis(valuation_report, preprocessed_data)
        closing_remarks = self._build_closing_remarks()
        
        # Combine sections into full email body
        email_body = f"""{introduction}

{valuation_summary}

{corroborating_section}

{market_analysis}

{closing_remarks}"""
        
        # Generate subject line
        verdict = valuation_report.get('analysis_summary', {}).get('verdict', 'FAIR').upper()
        estimated_val = valuation_report.get('analysis_summary', {}).get('estimated_value', '$0')
        subject = f"Property Valuation Report: {verdict} at {estimated_val}"
        
        return {
            "subject": subject,
            "body": email_body
        }
        
        print(f"📊 Selected properties for email: {len(selected_properties)}")
        
        # Build email sections
        introduction = self._build_introduction(recipient_name, target_property)
        valuation_summary = self._build_valuation_summary(valuation_report, target_property)
        corroborating_section = self._build_corroborating_properties_section(selected_properties)
        market_analysis = self._build_market_analysis(valuation_report, preprocessed_data)
        closing_remarks = self._build_closing_remarks()
        
        # Combine sections into full email body
        email_body = f"""{introduction}

{valuation_summary}

{corroborating_section}

{market_analysis}

{closing_remarks}"""
        
        # Generate subject line
        verdict = valuation_report.get('analysis_summary', {}).get('verdict', 'FAIR').upper()
        estimated_val = valuation_report.get('analysis_summary', {}).get('estimated_value', '$0')
        subject = f"Property Valuation Report: {verdict} at {estimated_val}"
        
        print(f"✅ Email generated successfully")
        print(f"   Subject: {subject}")
        print(f"   Body length: {len(email_body)}")
        
        # Return subject and body
        return {
            "subject": subject,
            "body": email_body
        }
    
    def _generate_email_with_feedback(self, state: dict, recipient_name: str, user_feedback: str, previous_email: dict, feedback_history: list) -> dict:
        """Generate improved email based on user feedback using LLM"""
        
        print(f"🔄 Incorporating user feedback: {user_feedback[:100]}...")
        
        # Extract required data from state
        valuation_report = state.get('valuation_report', {})
        preprocessed_data = state.get('preprocessed_data', {})
        target_property = state.get('target_property', {})
        selected_properties = state.get('selected_properties', [])
        
        try:
            # Prepare comparable properties for the prompt
            comparable_properties = self._format_comparables_for_prompt(selected_properties)
            
            # Prepare valuation summary for prompt
            analysis_summary = valuation_report.get('analysis_summary', {})
            valuation_summary = f"""
Estimated Value: {analysis_summary.get('estimated_value', 'N/A')}
Asking Price: ${target_property.get('asking_price', 0):,}
Verdict: {analysis_summary.get('verdict', 'FAIRLY_PRICED').upper()}
Variance: {analysis_summary.get('variance_percent', '0%')}
Rationale: {analysis_summary.get('why_this_price', 'Based on market analysis')}
"""
            
            # Build feedback context
            feedback_context = f"""
PREVIOUS EMAIL:
Subject: {previous_email.get('subject', '')}
Body: {previous_email.get('body', '')}

USER FEEDBACK: {user_feedback}

FEEDBACK HISTORY:
{chr(10).join([f"Iteration {h['iteration']}: {h['feedback']}" for h in feedback_history[-3:]])}
"""
            
            # Create enhanced prompt
            enhanced_prompt = EMAIL_GENERATION_PROMPT + f"""

SPECIAL INSTRUCTIONS FOR IMPROVEMENT:
You are improving an existing email based on user feedback. 

{feedback_context}

INSTRUCTIONS:
1. Read the user feedback carefully
2. Apply the requested changes while maintaining professionalism
3. Keep the same factual information (property details, valuation, comparables)
4. Adjust tone, style, length, or emphasis based on feedback
5. Still follow all the original formatting rules (10 lines max, no headers, etc.)

Generate the IMPROVED email addressing the user's feedback:
"""

            # Get prompt template and format it
            from prompts.emailGenerationPrompt import get_email_generation_prompt_template
            
            # Create template variables
            template_vars = {
                'target_property_details': f"{target_property.get('address', 'Unknown')} - {target_property.get('bedrooms', 0)} bed, {target_property.get('bathrooms', 0)} bath, {target_property.get('sqft', 0)} sqft - Asking: ${target_property.get('asking_price', 0):,}",
                'valuation_summary': valuation_summary.strip(),
                'comparable_properties': comparable_properties
            }
            
            # Instead of using the template, create a direct prompt that includes feedback
            direct_prompt = f"""You are a professional real estate valuation expert. IMPROVE the existing email based on user feedback.

TARGET PROPERTY: {template_vars['target_property_details']}
VALUATION: {template_vars['valuation_summary']}
COMPARABLES: {template_vars['comparable_properties']}

{feedback_context}

Create a SHORT, PUNCHY email explaining property valuation in under 10 lines.

STRICT REQUIREMENTS:
1. Max 10 lines total - be brutally concise
2. NO headers, NO sections, NO markdown formatting
3. NO confidence level mention (it's redundant)
4. NO repeated headers like "Market Analysis:" or "Recommendations:" 
5. Plain paragraph format only
6. Include property names as clickable links in body: [Property Address](URL)
7. Subject: Under 10 words, specific, professional

APPLY USER FEEDBACK: {user_feedback}

Generate the improved email addressing the feedback while maintaining professionalism and factual accuracy:
"""

            # Get LLM response
            response = self.llm.invoke(direct_prompt)
            response_text = response.content.strip()
            
            # Parse the response to extract subject and body
            if "Subject:" in response_text:
                lines = response_text.split('\n')
                subject_line = ""
                body_lines = []
                found_subject = False
                
                for line in lines:
                    if line.strip().lower().startswith('subject:'):
                        subject_line = line.replace('Subject:', '').replace('subject:', '').strip()
                        found_subject = True
                    elif found_subject and line.strip():
                        body_lines.append(line)
                
                subject = subject_line if subject_line else f"Property Valuation Update - {target_property.get('address', '')}"
                body = '\n'.join(body_lines).strip()
            else:
                # Fallback: use first line as subject, rest as body
                lines = response_text.split('\n')
                subject = lines[0].strip() if lines else "Property Valuation Update"
                body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else response_text
            
            print(f"✅ Improved email generated with feedback")
            print(f"   Subject: {subject}")
            print(f"   Body length: {len(body)}")
            
            return {
                "subject": subject,
                "body": body
            }
            
        except Exception as e:
            print(f"❌ Error generating email with feedback: {str(e)}")
            # Fallback to original email
            return previous_email
    
    def _build_introduction(self, recipient_name: str, target_property: dict) -> str:
        """Build professional introduction section"""
        
        address = target_property.get('address', 'the property')
        
        return f"""Dear {recipient_name},

Thank you for the opportunity to provide a comprehensive market valuation analysis of your property. 

Below is a detailed professional valuation report for {address}, including a comparative market analysis based on recent comparable sales in the area.
"""
    
    def _build_valuation_summary(self, valuation_report: dict, target_property: dict) -> str:
        """Build valuation summary section"""
        
        summary = valuation_report.get('analysis_summary', {})
        estimated = summary.get('estimated_value', 'N/A')
        verdict = summary.get('verdict', 'FAIRLY PRICED').upper()
        variance = summary.get('variance_percent', '0%')
        asking_price = target_property.get('asking_price', 0)
        why_price = summary.get('why_this_price', 'Based on comprehensive market analysis.')
        confidence = summary.get('confidence_level', 'Unknown').upper()
        
        return f"""VALUATION SUMMARY
═══════════════════════════════════════════════════════════════

Estimated Market Value: {estimated}
Asking Price: ${asking_price:,}
Market Position: {verdict}
Variance: {variance}
Confidence Level: {confidence}

VALUATION RATIONALE:
{why_price}
"""
    
    def _build_corroborating_properties_section(self, selected_properties: list) -> str:
        """
        Build corroborating properties section with selected properties and links
        
        This section shows the specific properties that the user selected for analysis
        """
        
        if not selected_properties:
            return """CORROBORATING PROPERTIES
═══════════════════════════════════════════════════════════════

No corroborating properties were selected for this analysis. 
To add comparable properties, please select them from the property cards in the application.
"""
        
        header = f"""CORROBORATING PROPERTIES
═══════════════════════════════════════════════════════════════

The following {len(selected_properties)} properties have been selected and analyzed as market comparables:

"""
        
        property_lines = []
        for idx, prop in enumerate(selected_properties, 1):
            address = prop.get('address', 'Unknown Address')
            price = prop.get('price', 0)
            beds = prop.get('bedrooms', 'N/A')
            baths = prop.get('bathrooms', 'N/A')
            sqft = prop.get('living_area_sqft', 'N/A')
            ppsf = prop.get('price_per_sqft', 0)
            status = prop.get('home_status', 'unknown').upper()
            url = prop.get('url', '')
            
            # Format property with link
            if url:
                prop_line = f"{idx}. {address} - {status}"
                prop_line += f"\n   Price: ${price:,} | Beds: {beds} | Baths: {baths} | Sqft: {sqft:,}"
                prop_line += f"\n   Price/sqft: ${ppsf:.2f}"
                prop_line += f"\n   Link: {url}"
            else:
                prop_line = f"{idx}. {address} - {status}"
                prop_line += f"\n   Price: ${price:,} | Beds: {beds} | Baths: {baths} | Sqft: {sqft:,}"
                prop_line += f"\n   Price/sqft: ${ppsf:.2f}"
            
            property_lines.append(prop_line)
        
        properties_text = "\n\n".join(property_lines)
        
        summary = f"""
Analysis of these properties demonstrates consistent pricing in the current market.
The average price per square foot of these comparables informs our valuation estimate.
"""
        
        return header + properties_text + summary
    
    def _build_market_analysis(self, valuation_report: dict, preprocessed_data: dict) -> str:
        """Build market analysis section"""
        
        market = valuation_report.get('market_analysis', {})
        stats = preprocessed_data.get('market_statistics', {})
        
        trend = market.get('trend', 'Stable').upper()
        inventory = market.get('inventory_status', 'Moderate').upper()
        days_avg = market.get('days_on_market_avg', 30)
        
        ppsf_avg = stats.get('price_per_sqft_avg', 0)
        ppsf_min = stats.get('price_per_sqft_min', 0)
        ppsf_max = stats.get('price_per_sqft_max', 0)
        
        return f"""MARKET ANALYSIS
═══════════════════════════════════════════════════════════════

Market Trend: {trend}
Inventory Status: {inventory}
Average Days on Market: {days_avg} days

Price Per Square Foot Analysis:
  • Market Average: ${ppsf_avg:.2f}/sqft
  • Range: ${ppsf_min:.2f} - ${ppsf_max:.2f}/sqft

This analysis is based on recent comparable sales data in the local market.
"""
    
    def _build_closing_remarks(self) -> str:
        """Build professional closing remarks"""
        
        return """CLOSING REMARKS
═══════════════════════════════════════════════════════════════

This valuation report provides a comprehensive market analysis based on comparable 
recent sales and current market conditions. The estimated value represents our 
professional opinion of the property's fair market value.

For questions or to discuss this valuation further, please don't hesitate to contact us.

Best regards,
Real Estate Analysis Team
"""
    
    def _format_comparables_for_prompt(self, selected_properties: list) -> str:
        """Format comparable properties for use in LLM prompts"""
        
        if not selected_properties:
            return "No comparable properties selected."
        
        comparables = []
        for idx, prop in enumerate(selected_properties, 1):
            address = prop.get('address', 'Unknown Address')
            price = prop.get('price', 0)
            beds = prop.get('bedrooms', 'N/A')
            baths = prop.get('bathrooms', 'N/A')
            sqft = prop.get('living_area_sqft', 'N/A')
            ppsf = prop.get('price_per_sqft', 0)
            status = prop.get('home_status', 'unknown').upper()
            url = prop.get('url', '')
            
            comp_line = f"{idx}. {address} - ${price:,} | {beds}bed/{baths}bath | {sqft}sqft | ${ppsf:.2f}/sqft | {status}"
            if url:
                comp_line += f" | {url}"
            comparables.append(comp_line)
        
        return '\n'.join(comparables)
    
    def _extract_email_from_text(self, text: str) -> dict:
        """
        Extract subject and body from plain text email response
        Handles cases where LLM returns formatted email instead of JSON
        
        Args:
            text: Plain text response from LLM
        
        Returns:
            Dict with 'subject' and 'body' extracted from text
        """
        
        email_data = {"subject": "", "body": ""}
        
        # Look for subject line patterns
        lines = text.split('\n')
        
        # Pattern 1: **Subject: ...** (bold markdown)
        for i, line in enumerate(lines):
            if '**Subject:' in line or '*Subject:' in line:
                # Extract subject from the line
                subject = line.replace('**Subject:', '').replace('**', '').replace('*Subject:', '').replace('*', '').strip()
                if subject:
                    email_data['subject'] = subject
                    # Body starts after subject
                    email_data['body'] = '\n'.join(lines[i+1:]).strip()
                    break
            elif 'Subject:' in line and not line.startswith('#'):
                # Plain text subject
                subject = line.replace('Subject:', '').strip()
                if subject and len(subject) > 5:  # Real subject, not a false positive
                    email_data['subject'] = subject
                    email_data['body'] = '\n'.join(lines[i+1:]).strip()
                    break
        
        # If no subject found, try to extract from first meaningful line
        if not email_data['subject'] and lines:
            # Find first non-empty line as subject (usually contains email content)
            for line in lines:
                if line.strip() and len(line.strip()) > 10 and not line.startswith('Here'):
                    email_data['subject'] = line.strip()[:100]  # Max 100 chars
                    break
        
        # Clean up body - remove markdown formatting
        if email_data['body']:
            email_data['body'] = email_data['body'].replace('**', '').replace('*', '')
        else:
            # If no body extracted yet, use everything after subject
            email_data['body'] = '\n'.join(lines[1:]).replace('**', '').replace('*', '').strip()
        
        # Fallback if both are empty
        if not email_data['subject']:
            email_data['subject'] = 'Property Valuation Email'
        if not email_data['body']:
            email_data['body'] = text  # Use full text as fallback
        
        print(f"   🔄 Extracted from plain text:")
        print(f"      Subject: {email_data['subject'][:60]}...")
        print(f"      Body length: {len(email_data['body'])}")
        
        return email_data

