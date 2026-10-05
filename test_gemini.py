#!/usr/bin/env python
"""Quick test to verify Gemini API connectivity."""

import google.generativeai as genai
from app.config import settings

def test_gemini():
    """Test Gemini API connection."""
    try:
        if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key":
            print("❌ GEMINI_API_KEY not set in .env")
            print("\n💡 Get your free API key:")
            print("   1. Visit: https://aistudio.google.com/app/apikey")
            print("   2. Click 'Create API Key'")
            print("   3. Add to .env: GEMINI_API_KEY=your_key_here")
            return False
        
        print(f"🔍 Testing Gemini API with model: {settings.ai_model}")
        genai.configure(api_key=settings.gemini_api_key)
        
        # Test with a simple prompt
        model = genai.GenerativeModel(settings.ai_model)
        response = model.generate_content("Say 'API works!' in exactly two words.")
        
        print(f"✅ Gemini API connection successful!")
        print(f"📝 Test response: {response.text}")
        print(f"🎯 Model: {settings.ai_model}")
        return True
        
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        print("\n💡 Check:")
        print("   - API key is valid and not expired")
        print("   - Model name is correct (gemini-2.0-flash-exp, gemini-1.5-pro)")
        print("   - Internet connection is working")
        return False

if __name__ == "__main__":
    test_gemini()
