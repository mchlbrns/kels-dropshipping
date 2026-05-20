import os
import sys
import requests

def main():
    print("==================================================")
    print("  🛍️ Kels Dropshipping - CJ Access Token Fetcher")
    print("==================================================")
    
    # Check if API Key is already set in environment
    api_key = os.environ.get('CJ_API_KEY')
    if not api_key:
        api_key = input("👉 Enter your CJ API Key: ").strip()
        
    if not api_key:
        print("❌ Error: API Key is required.")
        return

    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {"Content-Type": "application/json"}
    payload = {"apiKey": api_key}
    
    print("\nSending request to CJ Dropshipping API...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # CJ API returns status in 'code' or boolean in 'result'
            if data.get("code") == 200 or data.get("result") is True:
                result_data = data.get("data", {})
                access_token = result_data.get("accessToken")
                refresh_token = result_data.get("refreshToken")
                expiry_date = result_data.get("accessTokenExpiryDate")
                
                print("\n🎉 Success! CJ Dropshipping Credentials Received:")
                print("-" * 50)
                print(f"🔑 Access Token : {access_token}")
                if refresh_token:
                    print(f"🔄 Refresh Token: {refresh_token}")
                if expiry_date:
                    print(f"📅 Expiry Date  : {expiry_date}")
                print("-" * 50)
                
                print("\n👉 What to do next:")
                print("1. Create/Open the `.env` file in your root workspace directory.")
                print("2. Paste the following configuration lines into your `.env`:")
                print(f"   CJ_API_KEY={api_key}")
                print(f"   CJ_ACCESS_TOKEN={access_token}")
                print("   CJ_USE_SANDBOX=False")
                print("\nNote: The access token is valid for 180 days.")
            else:
                print(f"\n❌ CJ API Error: {data.get('message', 'Unknown API error message')}")
                print(f"Raw Response: {data}")
        else:
            print(f"\n❌ HTTP Request Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"\n❌ Connection Error: {str(e)}")
        print("Ensure you have an active internet connection.")

if __name__ == "__main__":
    main()
