import torch
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from flask import current_app
import numpy as np

class EssayGrader:
    """BERT-based model for grading essays."""
    
    def __init__(self):
        """Initialize the BERT model and tokenizer."""
        try:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.tokenizer = BertTokenizer.from_pretrained(current_app.config['BERT_MODEL_PATH'])
            self.model = BertForSequenceClassification.from_pretrained(
                current_app.config['BERT_MODEL_PATH'],
                num_labels=5  # 5-point grading scale
            ).to(self.device)
            self.model.eval()
        except Exception as e:
            raise Exception(f"Error initializing BERT model: {str(e)}")

    def preprocess_text(self, text):
        """Preprocess essay text for BERT model."""
        try:
            # Tokenize and encode the text
            encoded = self.tokenizer.encode_plus(
                text,
                add_special_tokens=True,
                max_length=512,
                padding='max_length',
                truncation=True,
                return_attention_mask=True,
                return_tensors='pt'
            )
            return encoded
        except Exception as e:
            raise Exception(f"Error preprocessing text: {str(e)}")

    def grade_essay(self, essay_text, reference_answer):
        """
        Grade an essay using BERT model.
        Returns tuple of (score, feedback)
        """
        try:
            # Combine essay and reference for comparison
            combined_text = f"Reference: {reference_answer} Essay: {essay_text}"
            
            # Preprocess
            encoded = self.preprocess_text(combined_text)
            
            # Move to device
            input_ids = encoded['input_ids'].to(self.device)
            attention_mask = encoded['attention_mask'].to(self.device)
            
            # Get prediction
            with torch.no_grad():
                outputs = self.model(input_ids, attention_mask=attention_mask)
                predicted_score = torch.argmax(outputs.logits, dim=1).item() + 1  # Scale from 0-4 to 1-5
            
            # Generate feedback based on score
            feedback = self.generate_feedback(predicted_score, essay_text, reference_answer)
            
            return predicted_score, feedback
            
        except Exception as e:
            raise Exception(f"Error grading essay: {str(e)}")

    def generate_feedback(self, score, essay_text, reference_answer):
        """Generate detailed feedback based on the essay score and content."""
        try:
            feedback_templates = {
                5: "Excellent work! Your essay demonstrates comprehensive understanding and excellent articulation.",
                4: "Good work! Your essay shows strong understanding with some room for improvement.",
                3: "Satisfactory work. Your essay demonstrates basic understanding but needs more detail.",
                2: "Below average. Your essay needs significant improvement in content and structure.",
                1: "Needs improvement. Please review the topic and try again."
            }
            
            base_feedback = feedback_templates.get(score, "Invalid score")
            
            # Add specific feedback points
            specific_points = []
            
            # Length comparison
            if len(essay_text.split()) < len(reference_answer.split()) * 0.5:
                specific_points.append("Consider expanding your response with more details.")
            
            # Key terms check (simplified)
            ref_words = set(reference_answer.lower().split())
            essay_words = set(essay_text.lower().split())
            missing_key_terms = ref_words - essay_words
            if missing_key_terms:
                specific_points.append("Consider incorporating these key concepts: " + 
                                    ", ".join(list(missing_key_terms)[:3]))
            
            # Combine feedback
            detailed_feedback = base_feedback
            if specific_points:
                detailed_feedback += "\n\nSpecific suggestions:\n- " + "\n- ".join(specific_points)
            
            return detailed_feedback
            
        except Exception as e:
            raise Exception(f"Error generating feedback: {str(e)}")

class QuestionGenerator:
    """GPT-2 based model for generating exam questions."""
    
    def __init__(self):
        """Initialize the GPT-2 model and tokenizer."""
        try:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.tokenizer = GPT2Tokenizer.from_pretrained(current_app.config['GPT2_MODEL_PATH'])
            self.model = GPT2LMHeadModel.from_pretrained(
                current_app.config['GPT2_MODEL_PATH']
            ).to(self.device)
            self.model.eval()
        except Exception as e:
            raise Exception(f"Error initializing GPT-2 model: {str(e)}")

    def generate_question(self, topic, question_type='multiple_choice'):
        """
        Generate a question based on the given topic.
        Returns dict containing question details.
        """
        try:
            # Prepare prompt based on question type
            if question_type == 'multiple_choice':
                prompt = f"Generate a multiple choice question about {topic}:\nQuestion:"
            else:
                prompt = f"Generate an essay question about {topic}:\nQuestion:"
            
            # Encode prompt
            inputs = self.tokenizer.encode(prompt, return_tensors='pt').to(self.device)
            
            # Generate question
            outputs = self.model.generate(
                inputs,
                max_length=150,
                num_return_sequences=1,
                no_repeat_ngram_size=2,
                temperature=0.7,
                top_k=50,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Decode generated text
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Process the generated text based on question type
            if question_type == 'multiple_choice':
                return self._process_multiple_choice(generated_text, topic)
            else:
                return self._process_essay_question(generated_text, topic)
                
        except Exception as e:
            raise Exception(f"Error generating question: {str(e)}")

    def _process_multiple_choice(self, generated_text, topic):
        """Process generated text into a multiple choice question format."""
        try:
            # Split into question and options
            parts = generated_text.split('\n')
            question = parts[0].replace('Question:', '').strip()
            
            # Generate options if not present in generated text
            options = []
            correct_answer = None
            
            if len(parts) < 2:
                # Generate options using the model
                options_prompt = f"Generate 4 options for the question: {question}\nOptions:"
                inputs = self.tokenizer.encode(options_prompt, return_tensors='pt').to(self.device)
                
                outputs = self.model.generate(
                    inputs,
                    max_length=200,
                    num_return_sequences=1,
                    no_repeat_ngram_size=2,
                    temperature=0.7
                )
                
                options_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                options = [opt.strip() for opt in options_text.split('\n') if opt.strip()][:4]
                correct_answer = options[0]  # First option as correct answer
            else:
                options = [opt.strip() for opt in parts[1:] if opt.strip()][:4]
                correct_answer = options[0]
            
            return {
                'question_text': question,
                'question_type': 'multiple_choice',
                'options': options,
                'correct_answer': correct_answer
            }
            
        except Exception as e:
            raise Exception(f"Error processing multiple choice question: {str(e)}")

    def _process_essay_question(self, generated_text, topic):
        """Process generated text into an essay question format."""
        try:
            # Clean up generated text
            question = generated_text.replace('Question:', '').strip()
            
            # Generate a reference answer for grading
            reference_prompt = f"Write a model answer for the question: {question}"
            inputs = self.tokenizer.encode(reference_prompt, return_tensors='pt').to(self.device)
            
            outputs = self.model.generate(
                inputs,
                max_length=300,
                num_return_sequences=1,
                no_repeat_ngram_size=2,
                temperature=0.7
            )
            
            reference_answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return {
                'question_text': question,
                'question_type': 'essay',
                'reference_answer': reference_answer
            }
            
        except Exception as e:
            raise Exception(f"Error processing essay question: {str(e)}")

# Singleton instances
essay_grader = None
question_generator = None

def get_essay_grader():
    """Get or create the EssayGrader instance."""
    global essay_grader
    if essay_grader is None:
        essay_grader = EssayGrader()
    return essay_grader

def get_question_generator():
    """Get or create the QuestionGenerator instance."""
    global question_generator
    if question_generator is None:
        question_generator = QuestionGenerator()
    return question_generator
