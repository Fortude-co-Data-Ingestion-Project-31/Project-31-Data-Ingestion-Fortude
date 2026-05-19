import requests

def test_my_jira_endpoint():
    # The URL where your FastAPI server is running
    field_url = "http://127.0.0.1:8000/jira/get_fields"
    issue_url = "http://127.0.0.1:8000/jira/my_issues"
    
    print(f"Testing endpoint: {field_url}...")
    try:
       
        response = requests.get(field_url)
        
        # Check if the FastAPI backend returned a success
        if response.status_code == 200:
            data = response.json()
            
            print("Successfully connected to FastAPI!")
            print("fleid data")
            print(data)
        else:
            print(f"Failed! Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the FastAPI server. Is it running?")

    try:
       
        response = requests.get(issue_url)
        
        # Check if the FastAPI backend returned a success
        if response.status_code == 200:
            data = response.json()
            issues = data.get("issues", [])
            
            print("Successfully connected to FastAPI!")
            print(f"Found {len(issues)} issues assigned to you.\n")
            
            for issue in issues:
                print(f" - {issue['key']}: {issue['fields']['summary']}")
            print("below is the full data")
            print(data)
        else:
            print(f"Failed! Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the FastAPI server. Is it running?")

if __name__ == "__main__":
    test_my_jira_endpoint()