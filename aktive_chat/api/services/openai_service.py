import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

def translate_text(text, target_language):
    """
    Translate text using OpenAI's GPT model
    
    Args:
        text (str): Text to translate
        target_language (str): Target language for translation
        
    Returns:
        str: Translated text
    """
    # OpenAI API key should be set in environment
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key not found in environment variables")
    
    translation_template = """
    Translate the following sentence into {language}, return ONLY the translation, nothing else.

    Sentence: {sentence}
    """
    
    output_parser = StrOutputParser()
    llm = ChatOpenAI(temperature=0.0, model="gpt-4-turbo")
    translation_prompt = ChatPromptTemplate.from_template(translation_template)

    translation_chain = (
        {"language": RunnablePassthrough(), "sentence": RunnablePassthrough()} 
        | translation_prompt
        | llm
        | output_parser
    )
    
    data_input = {"language": target_language, "sentence": text}
    translation = translation_chain.invoke(data_input)
    
    return translation