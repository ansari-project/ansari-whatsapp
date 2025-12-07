"""
Script to check WhatsApp Business Account subscriptions and phone numbers.

Usage:
    python path/to/this/file.py

Requirements:
    - Set up your .env file with META_ACCESS_TOKEN_FROM_SYS_USER / WABA ID 
        (otherwise you'll be prompted at runtime)

Features:
    - Understand the big picture (relation between WABA, apps, etc)
    - Get WABA details (name, ID, etc.)
    - List subscribed apps
    - List phone numbers
    - Subscribe WABA to app
    - Unsubscribe WABA from app
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
dotenv_loaded = load_dotenv()

# Configuration
META_API_VERSION = "v22.0"

# Check if .env file was loaded
if dotenv_loaded:
    ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN_FROM_SYS_USER")
    WABA_ID = os.getenv("META_WABA_ID")  # Can be None, will prompt if not set
else:
    # No .env file found, will prompt user for values
    ACCESS_TOKEN = None
    WABA_ID = None  

def get_waba_details():
    """Get WABA details including name and other information."""
    print("\n" + "="*60)
    print("FETCHING WABA DETAILS")
    print("="*60)

    url = f"https://graph.facebook.com/{META_API_VERSION}/{WABA_ID}"
    params = {
        "fields": "id,name,timezone_id,message_template_namespace,account_review_status"
    }
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        print(f"\nWABA Details:")
        print(f"   ID: {data.get('id', 'N/A')}")
        print(f"   Name: {data.get('name', 'N/A')}")
        print(f"   Timezone: {data.get('timezone_id', 'N/A')}")
        print(f"   Namespace: {data.get('message_template_namespace', 'N/A')}")
        print(f"   Review Status: {data.get('account_review_status', 'N/A')}")

        return data

    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP Error: {e}")
        print(f"   Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"\nError: {e}")
        return None


def debug_access_token():
    """View the access token details including app, permissions, and expiration."""
    print("\n" + "="*60)
    print("VIEWING ACCESS TOKEN DETAILS")
    print("="*60)

    url = f"https://graph.facebook.com/{META_API_VERSION}/debug_token"
    params = {
        "input_token": ACCESS_TOKEN,
        "access_token": ACCESS_TOKEN  # Can use the same token to debug itself
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        result = response.json()

        if "data" in result:
            data = result["data"]
            from datetime import datetime

            print("\nAccess Token Details:")

            # Basic app info
            print(f"   App ID: {data.get('app_id', 'N/A')}")
            print(f"   Application: {data.get('application', 'N/A')}")
            print(f"   Type: {data.get('type', 'N/A')}")
            print(f"   Is Valid: {data.get('is_valid', 'N/A')}")

            # Time-related fields
            issued_at = data.get('issued_at')
            if issued_at:
                issued_date = datetime.fromtimestamp(issued_at)
                print(f"   Issued At: {issued_date} ({issued_at})")
            else:
                print(f"   Issued At: N/A")

            # Check expiration
            expires_at = data.get('expires_at', 0)
            if expires_at == 0:
                print("   Expires At: Never (permanent token)")
            else:
                expiry_date = datetime.fromtimestamp(expires_at)
                print(f"   Expires At: {expiry_date} ({expires_at})")

            # Data access expiration
            data_access_expires = data.get('data_access_expires_at')
            if data_access_expires:
                data_expiry = datetime.fromtimestamp(data_access_expires)
                print(f"   Data Access Expires At: {data_expiry} ({data_access_expires})")

            # User/Profile info
            if 'user_id' in data:
                print(f"   User ID: {data.get('user_id')}")
            if 'profile_id' in data:
                print(f"   Profile ID: {data.get('profile_id')}")

            # Show scopes/permissions
            scopes = data.get('scopes', [])
            if scopes:
                print(f"   Permissions/Scopes ({len(scopes)}):")
                for scope in scopes:
                    print(f"      - {scope}")
            else:
                print(f"   Permissions/Scopes: None (may be an app token)")

            # Granular scopes (more detailed permissions)
            granular_scopes = data.get('granular_scopes', [])
            if granular_scopes:
                print(f"   Granular Scopes ({len(granular_scopes)}):")
                for scope in granular_scopes:
                    if isinstance(scope, dict):
                        print(f"      - {scope.get('scope', 'N/A')}: {scope.get('target_ids', [])}")
                    else:
                        print(f"      - {scope}")

            # Metadata (additional info like SSO)
            metadata = data.get('metadata')
            if metadata:
                print(f"   Metadata:")
                if isinstance(metadata, dict):
                    for key, value in metadata.items():
                        print(f"      {key}: {value}")
                else:
                    print(f"      {metadata}")

            # Error field (if token is invalid)
            if 'error' in data:
                print(f"   Error: {data.get('error')}")

            # Show any additional fields not explicitly handled
            handled_keys = {
                'app_id', 'application', 'type', 'is_valid', 'issued_at',
                'expires_at', 'data_access_expires_at', 'user_id', 'profile_id',
                'scopes', 'granular_scopes', 'metadata', 'error'
            }
            additional_fields = {k: v for k, v in data.items() if k not in handled_keys}
            if additional_fields:
                print(f"   Additional Fields:")
                for key, value in additional_fields.items():
                    print(f"      {key}: {value}")

        return result

    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP Error: {e}")
        print(f"   Response: {e.response.text}")
        print("\n   Note: debug_token may not work on development/test apps.")
        print("   Try checking your token at: https://developers.facebook.com/tools/debug/accesstoken/")
        return None
    except Exception as e:
        print(f"\nError: {e}")
        return None


def check_subscribed_apps():
    """Check which apps are subscribed to the WABA."""
    print("\n" + "="*60)
    print("CHECKING SUBSCRIBED APPS")
    print("="*60)

    url = f"https://graph.facebook.com/{META_API_VERSION}/{WABA_ID}/subscribed_apps"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        print("\nSuccessfully retrieved subscribed apps")

        if "data" in data:
            if len(data["data"]) == 0:
                print("\nWARNING: No apps are subscribed to this WABA!")
                print("   This means webhooks won't be delivered to your app.")
            else:
                # Extract app names for summary
                app_names = []
                for app in data["data"]:
                    if "whatsapp_business_api_data" in app:
                        app_name = app["whatsapp_business_api_data"].get("name", "Unknown App")
                        app_names.append(app_name)
                
                # Show summary with app names
                print(f"\nFound {len(data['data'])} subscribed app(s) to the WABA: {', '.join(app_names)}")
                
                # Show detailed information for each app
                for app in data["data"]:
                    print("\n   App Details:")
                    for key, value in app.items():
                        print(f"      {key}: {value}")

        return data

    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP Error: {e}")
        print(f"   Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"\nError: {e}")
        return None


def list_phone_numbers():
    """List all phone numbers registered to the WABA."""
    print("\n" + "="*60)
    print("LISTING PHONE NUMBERS")
    print("="*60)

    url = f"https://graph.facebook.com/{META_API_VERSION}/{WABA_ID}/phone_numbers"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        print(f"\nSuccessfully retrieved phone numbers for WABA: {WABA_ID}")

        if "data" in data:
            print(f"\nFound {len(data['data'])} phone number(s):")
            for phone in data["data"]:
                print(f"\n   Phone Number ID: {phone.get('id')}")
                print(f"   Display Name: {phone.get('display_phone_number', 'N/A')}")
                print(f"   Verified Name: {phone.get('verified_name', 'N/A')}")
                print(f"   Quality Rating: {phone.get('quality_rating', 'N/A')}")
                print(f"   Status: {phone.get('code_verification_status', 'N/A')}")
        else:
            print("\nNo phone numbers found for this WABA")

        return data

    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP Error: {e}")
        print(f"   Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"\nError: {e}")
        return None


def subscribe_waba():
    """Subscribe the WABA to receive webhooks in this app."""
    print("\n" + "="*60)
    print("SUBSCRIBING WABA TO APP")
    print("="*60)

    url = f"https://graph.facebook.com/{META_API_VERSION}/{WABA_ID}/subscribed_apps"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    print("\nThis will subscribe your WABA to the app associated with your access token.")
    print("   Webhooks from this WABA will be sent to this app's webhook URL.")
    user_response = input("\n   Do you want to proceed? (yes/no): ").strip().lower()

    if user_response != "yes":
        print("   Subscription cancelled.")
        return None

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        print("\nSuccessfully subscribed WABA to app!")
        if data.get("success"):
            print("   Status: Subscription active")

        return data

    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP Error: {e}")
        print(f"   Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"\nError: {e}")
        return None


def unsubscribe_waba():
    """Unsubscribe the WABA from receiving webhooks in this app."""
    print("\n" + "="*60)
    print("UNSUBSCRIBING WABA FROM APP")
    print("="*60)

    # Step 1: Get the current access token's app name
    print("\n→ Step 1: Identifying your access token's app...")
    token_debug_url = f"https://graph.facebook.com/{META_API_VERSION}/debug_token"
    token_params = {
        "input_token": ACCESS_TOKEN,
        "access_token": ACCESS_TOKEN
    }
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    try:
        token_response = requests.get(token_debug_url, params=token_params)
        token_response.raise_for_status()
        token_data = token_response.json()

        if "data" not in token_data:
            print("   ERROR: Unable to debug access token.")
            return None

        token_app_name = token_data["data"].get("application", "Unknown")
        token_app_id = token_data["data"].get("app_id", "Unknown")
        print(f"   Your access token is associated with: {token_app_name} (ID: {token_app_id})")

    except Exception as e:
        print(f"   ERROR: Failed to get token details: {e}")
        return None

    # Step 2: Get WABA name
    print("\n→ Step 2: Getting WABA details...")
    waba_url = f"https://graph.facebook.com/{META_API_VERSION}/{WABA_ID}"
    waba_params = {"fields": "name"}

    try:
        waba_response = requests.get(waba_url, headers=headers, params=waba_params)
        waba_response.raise_for_status()
        waba_data = waba_response.json()
        waba_name = waba_data.get("name", f"WABA {WABA_ID}")
        print(f"   WABA Name: {waba_name}")

    except Exception as e:
        print(f"   Warning: Could not get WABA name: {e}")
        waba_name = f"WABA {WABA_ID}"

    # Step 3: Get currently subscribed apps
    print("\n→ Step 3: Checking currently subscribed apps...")
    subscribed_url = f"https://graph.facebook.com/{META_API_VERSION}/{WABA_ID}/subscribed_apps"

    try:
        subscribed_response = requests.get(subscribed_url, headers=headers)
        subscribed_response.raise_for_status()
        subscribed_data = subscribed_response.json()

        if "data" not in subscribed_data or len(subscribed_data["data"]) == 0:
            print("   No apps are currently subscribed to this WABA.")
            print("\n   Nothing to unsubscribe. Exiting.")
            return None

        # Extract subscribed app names
        subscribed_app_names = []
        for app in subscribed_data["data"]:
            if "whatsapp_business_api_data" in app:
                app_name = app["whatsapp_business_api_data"].get("name", "Unknown App")
                subscribed_app_names.append(app_name)

        print(f"   Currently subscribed apps: {', '.join(subscribed_app_names) if subscribed_app_names else 'None found'}")

    except Exception as e:
        print(f"   ERROR: Failed to get subscribed apps: {e}")
        return None

    # Step 4: Check if token's app is in the subscribed list
    print("\n→ Step 4: Verifying subscription match...")

    if token_app_name not in subscribed_app_names:
        print("\n   WARNING: Your access token's app is NOT in the subscribed list!")
        print(f"\n   Details:")
        print(f"      * Your token is for: {token_app_name}")
        print(f"      * WABA '{waba_name}' is subscribed to: {', '.join(subscribed_app_names)}")
        print(f"\n   Cannot proceed with unsubscription.")
        print(f"\n   → Solution: Change your access token to one bound to an app in the subscribed list.")
        print(f"      Apps you need a token for:")
        for app_name in subscribed_app_names:
            print(f"         - {app_name}")
        return None

    # Step 5: Confirm unsubscription
    print(f"\n   Match found: {token_app_name} app is subscribed to {waba_name} WABA")
    print(f"\n→ Step 5: Confirming unsubscription...")
    print(f"\n   WARNING: This will unsubscribe '{token_app_name}' from '{waba_name}'")
    print(f"      * Webhooks will STOP being sent to {token_app_name}'s webhook URL")
    print(f"      * Other subscribed apps will remain unaffected: {', '.join([n for n in subscribed_app_names if n != token_app_name])}")

    user_response = input("\n   Are you sure you want to proceed? (yes/no): ").strip().lower()

    if user_response != "yes":
        print("   Unsubscription cancelled.")
        return None

    # Step 6: Perform unsubscription
    print("\n→ Step 6: Performing unsubscription...")
    try:
        response = requests.delete(subscribed_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        print(f"\n   Successfully unsubscribed '{token_app_name}' from '{waba_name}'!")
        if data.get("success"):
            print("   Status: Subscription removed")

        return data

    except requests.exceptions.HTTPError as e:
        print(f"\n   HTTP Error: {e}")
        print(f"      Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"\n   Error: {e}")
        return None


def show_prerequisite_knowledge():
    """Display prerequisite knowledge about Meta's WhatsApp Business architecture."""
    print("\n" + "="*60)
    print("PREREQUISITE KNOWLEDGE: Meta WhatsApp Business Architecture")
    print("="*60)

    print("\n📚 THE BIG PICTURE\n")

    print("1. HIERARCHY OF META ASSETS:")
    print("   " + "-"*56)
    print("   Meta Business Manager (business.facebook.com)")
    print("      ↓")
    print("   WhatsApp Business Account (WABA)")
    print("      ↓")
    print("   Phone Numbers (up to 20 per WABA)")
    print("\n   Developer App (developers.facebook.com)")
    print("      ↓")
    print("   App Secret + Access Token")
    print("      ↓")
    print("   Webhook URL (receives messages)")

    print("\n2. HOW THEY CONNECT:")
    print("   " + "-"*56)
    print("   • A WABA can be SUBSCRIBED to multiple Developer Apps")
    print("   • When someone messages your WhatsApp number:")
    print("      1. Meta finds which WABA owns that phone number")
    print("      2. Meta checks which Developer Apps are subscribed to that WABA")
    print("      3. Meta sends webhooks to ALL subscribed apps' webhook URLs")
    print("      4. Meta signs each webhook with the app's App Secret")

    print("\n3. KEY CONCEPTS:")
    print("   " + "-"*56)
    print("   • WABA (WhatsApp Business Account):")
    print("      - Container for your WhatsApp phone numbers")
    print("      - Managed in Meta Business Manager")
    print("      - Can have multiple phone numbers")
    print("\n   • Developer App (e.g., 'Ansari - Test'):")
    print("      - Created at developers.facebook.com")
    print("      - Has unique App ID and App Secret")
    print("      - Needs to be SUBSCRIBED to a WABA to receive webhooks")
    print("\n   • Access Token:")
    print("      - Generated for a specific Developer App")
    print("      - Used to authenticate API calls")
    print("      - Token is tied to ONE app only (cannot be shared)")
    print("\n   • App Secret:")
    print("      - Secret key unique to each Developer App")
    print("      - Used by Meta to sign webhook payloads")
    print("      - Your server verifies signatures to ensure authenticity")
    print("\n   • Subscription:")
    print("      - Links a WABA to a Developer App")
    print("      - Required for webhooks to be delivered")
    print("      - One WABA can subscribe to multiple apps")

    print("\n4. COMMON SETUP (3 ENVIRONMENTS):")
    print("   " + "-"*56)
    print("   • Test/Local Environment:")
    print("      - Developer App: 'Ansari - Test'")
    print("      - WABA: 'Test WhatsApp Business Account'")
    print("      - Phone Number: Test number (90-day expiry)")
    print("      - Webhook: zrok tunnel (e.g., https://xxx.share.zrok.io)")
    print("\n   • Staging Environment:")
    print("      - Developer App: 'Ansari - Staging'")
    print("      - WABA: Also 'Test WhatsApp Business Account'")
    print("      - Phone Number: Same Test number (nuisance though, as sending a msg to it hits both apps)")
    print("      - Webhook: Staging server URL")
    print("\n   • Production Environment:")
    print("      - Developer App: 'Ansari' (production)")
    print("      - WABA: Production WABA")
    print("      - Phone Number: Official business phone")
    print("      - Webhook: Production server URL")

    print("\n5. WHY THIS MATTERS:")
    print("   " + "-"*56)
    print("   • Access tokens are APP-SPECIFIC")
    print("      → You need separate tokens for test/staging/production")
    print("\n   • Subscriptions control webhook delivery")
    print("      → If not subscribed, you won't receive messages")
    print("\n   • App Secrets must match for signature verification")
    print("      → Wrong secret = webhooks rejected by your server")
    print("\n   • Multiple apps can subscribe to the same WABA")
    print("      → Useful for routing to different environments")

    print("\n6. VISUAL EXAMPLE:")
    print("   " + "-"*56)
    print("   WABA: 'Test WhatsApp Business Account'")
    print("      ├─ Phone: +1234567890 (test)")
    print("      └─ Subscribed to:")
    print("           ├─ App: 'Ansari - Test'")
    print("           │    ├─ Access Token: EAAMf...")
    print("           │    ├─ App Secret: abc123...")
    print("           │    └─ Webhook: https://xxx.share.zrok.io/whatsapp/v2")
    print("           └─ App: 'Ansari - Staging'")
    print("                ├─ Access Token: EAAMf...")
    print("                ├─ App Secret: def456...")
    print("                └─ Webhook: https://staging-api.ansari.chat/whatsapp/v2")
    print("\n   When user sends message to +1234567890:")
    print("      → Both 'Ansari - Test' AND 'Ansari - Staging' receive webhooks!")

    print("\n7. USEFUL RESOURCES:")
    print("   " + "-"*56)
    print("   • Debug Access Token:")
    print("      https://developers.facebook.com/tools/debug/accesstoken/")
    print("   • Meta Business Manager:")
    print("      https://business.facebook.com/")
    print("   • Developer Apps:")
    print("      https://developers.facebook.com/apps/")
    print("   • WhatsApp API Documentation:")
    print("      https://developers.facebook.com/docs/whatsapp/")

    print("\n" + "="*60)
    input("\nPress Enter to return to menu...")


def get_current_context():
    """Get and return current WABA name and App name for context display."""
    waba_name = "Unknown"
    app_name = "Unknown"

    # Get WABA name
    try:
        waba_url = f"https://graph.facebook.com/{META_API_VERSION}/{WABA_ID}"
        waba_params = {"fields": "name"}
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

        waba_response = requests.get(waba_url, headers=headers, params=waba_params)
        if waba_response.status_code == 200:
            waba_data = waba_response.json()
            waba_name = waba_data.get("name", "Unknown (probably invalid WABA ID)")
    except:
        pass  # Keep default "Unknown"

    # Get App name from token
    try:
        token_debug_url = f"https://graph.facebook.com/{META_API_VERSION}/debug_token"
        token_params = {
            "input_token": ACCESS_TOKEN,
            "access_token": ACCESS_TOKEN
        }

        token_response = requests.get(token_debug_url, params=token_params)
        if token_response.status_code == 200:
            token_data = token_response.json()
            if "data" in token_data:
                app_name = token_data["data"].get("application", "Unknown (probably invalid token)")
    except:
        pass  # Keep default "Unknown"

    return waba_name, app_name


def show_menu():
    """Display interactive menu for user actions."""
    # Get current context
    waba_name, app_name = get_current_context()

    print("\n" + "="*60)
    print("CURRENT CONTEXT")
    print("="*60)
    print(f"   WABA: {waba_name}")
    print(f"   App: {app_name}")
    print("="*60)
    print("AVAILABLE ACTIONS")
    print("="*60)
    print("\n0. 📚 Show prerequisite knowledge (understand the big picture)")
    print("1. View WABA details")
    print("2. View access token details for debugging")
    print("3. Check apps subscribed to the WABA")
    print("4. List phone numbers registered to the WABA")
    print("5. Subscribe WABA to app (enable webhooks)")
    print("6. Unsubscribe WABA from app (disable webhooks)")
    print("7. Run all checks (view everything)")
    print("8. Exit")

    while True:
        try:
            choice = input("\nEnter your choice (0-8): ").strip()
            if choice in ['0', '1', '2', '3', '4', '5', '6', '7', '8']:
                return choice
            else:
                print("   Invalid choice. Please enter a number between 0 and 8.")
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Exiting...")
            return '8'


def main():
    global ACCESS_TOKEN, WABA_ID  # Allow modification if not set in .env

    print("="*60)
    print("WhatsApp Business Account Subscription Manager")
    print("="*60)

    # Check if .env file was loaded
    if not dotenv_loaded:
        print("\n   No .env file found in the current directory")
        print("   You can either:")
        print("      1. Create a .env file with META_ACCESS_TOKEN_FROM_SYS_USER and META_WABA_ID")
        print("      2. Enter the values manually now (they won't be saved)")

        use_manual = input("\n   Enter values manually? (yes/no): ").strip().lower()
        if use_manual != "yes":
            print("\n   Please create a .env file and try again.")
            print("\n   Example .env file:")
            print("      META_ACCESS_TOKEN_FROM_SYS_USER=your_token_here")
            print("      META_WABA_ID=your_waba_id_here")
            return

    # Check for access token
    if not ACCESS_TOKEN:
        print("\n→ Access Token Configuration")
        print("   You can find your token at:")
        print("      1. Go to business.facebook.com → Business Settings → System Users")
        print("      2. Select your System User → Generate New Token")
        print("      3. Select your app and required permissions")
        print("      4. Copy the generated token")

        ACCESS_TOKEN = input("\n   Enter your META_ACCESS_TOKEN_FROM_SYS_USER: ").strip()

        if not ACCESS_TOKEN:
            print("\n   ERROR: Access token is required. Exiting...")
            return

    # Check for WABA ID (prompt if not set)
    if not WABA_ID:
        print("\n→ WABA ID Configuration")
        print("   You can find it at: developers.facebook.com → Your App → WhatsApp → API Setup")
        print("   Look for 'WhatsApp Business Account ID'")

        WABA_ID = input("\n   Enter your WABA ID: ").strip()

        if not WABA_ID:
            print("\n   ERROR: WABA ID is required. Exiting...")
            return

    print("\nConfiguration:")
    print(f"   WABA ID: {WABA_ID}")
    print(f"   Access Token: {ACCESS_TOKEN[:20]}...{ACCESS_TOKEN[-10:]}")

    # Interactive menu loop
    while True:
        choice = show_menu()

        if choice == '0':
            show_prerequisite_knowledge()
        elif choice == '1':
            get_waba_details()
        elif choice == '2':
            debug_access_token()
        elif choice == '3':
            check_subscribed_apps()
        elif choice == '4':
            list_phone_numbers()
        elif choice == '5':
            response = subscribe_waba()
            if response:
                print("\n   → Verifying subscription...")
                check_subscribed_apps()
        elif choice == '6':
            response = unsubscribe_waba()
            if response:
                print("\n   → Verifying unsubscription...")
                check_subscribed_apps()
        elif choice == '7':
            get_waba_details()
            debug_access_token()
            check_subscribed_apps()
            list_phone_numbers()
        elif choice == '8':
            print("\n" + "="*60)
            print("Done! Exiting...")
            print("="*60)
            break

        # Ask if user wants to continue
        if choice != '8':
            continue_choice = input("\n   Press Enter to return to menu (or 'q' to quit): ").strip().lower()
            if continue_choice == 'q':
                print("\n" + "="*60)
                print("Done! Exiting...")
                print("="*60)
                break


if __name__ == "__main__":
    main()
