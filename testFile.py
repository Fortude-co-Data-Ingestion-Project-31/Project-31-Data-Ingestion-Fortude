import requests

def test_my_jira_endpoint():
    # The URL where your FastAPI server is running
    local_url = "http://127.0.0.1:8000/jira/my_issues"
    
    print(f"Testing endpoint: {local_url}...")
    
    try:
        # We don't need Jira auth here because the FastAPI backend 
        # handles it internally!
        response = requests.get(local_url)
        
        # Check if the FastAPI backend returned a success
        if response.status_code == 200:
            data = response.json()
            issues = data.get("issues", [])
            
            print("Successfully connected to FastAPI!")
            print(f"Found {len(issues)} issues assigned to you.\n")
            
            for issue in issues:
                print(f" - {issue['key']}: {issue['fields']['summary']}")
        else:
            print(f"Failed! Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the FastAPI server. Is it running?")

if __name__ == "__main__":
    test_my_jira_endpoint()