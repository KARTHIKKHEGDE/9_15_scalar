try:
    from kiteconnect import KiteConnect
except ModuleNotFoundError:
    print("Installing required package 'kiteconnect'...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "kiteconnect"])
    from kiteconnect import KiteConnect

from kiteconnect.exceptions import TokenException
from pathlib import Path
from dotenv import load_dotenv
import os
import webbrowser
import time

def get_access_token():
    # Load environment variables
    env_path = Path(__file__).parent / 'secrets.env'
    if not load_dotenv(env_path):
        print(f"Error: Could not load .env file from {env_path}")
        return None
    
    # Get credentials from environment
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    
    if not all([api_key, api_secret]):
        print("Error: API_KEY and API_SECRET must be set in .env file")
        return None
    
    kite = KiteConnect(api_key=api_key)

    # Print and open login URL
    login_url = kite.login_url()
    print("\n1. Opening login URL in browser...")
    print(f"URL: {login_url}")
    webbrowser.open(login_url)

    # Get request token from user
    print("\n2. After logging in, you'll be redirected to a page.")
    print("From the redirect URL, copy the request_token parameter.")
    print("Example URL: https://redirect.url/?status=success&request_token=xxxxx")
    request_token = input("\nEnter request token: ").strip()

    try:
        print("\n3. Generating session...")
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        print("\nSuccess! Access token details:")
        print(f"Access Token: {access_token}")
        
        # Update .env file with new access token
        env_content = []
        if env_path.exists():
            with open(env_path) as f:
                env_content = f.readlines()
        
        # Update or add ACCESS_TOKEN
        token_updated = False
        for i, line in enumerate(env_content):
            if line.startswith('ACCESS_TOKEN='):
                env_content[i] = f'ACCESS_TOKEN={access_token}\n'
                token_updated = True
                break
        if not token_updated:
            env_content.append(f'ACCESS_TOKEN={access_token}\n')
        
        # Write back to .env
        with open(env_path, 'w') as f:
            f.writelines(env_content)
            
        print("\nAccess token saved to secrets.env file")
        return access_token

    except TokenException as e:
        print("\nError: Token is invalid or has expired!")
        print("Please try again with a fresh request token.")
        return None
    except Exception as e:
        print(f"\nError: {str(e)}")
        return None

if __name__ == "__main__":
    access_token = get_access_token()
    if access_token:
        print("\nYou can now use this access token in your trading script.")
