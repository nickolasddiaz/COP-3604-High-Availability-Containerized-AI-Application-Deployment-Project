def test_welcome_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Testing" in response.data

def test_new_chat_endpoint(client):
    response = client.post('/send/new', data={"message": "Hello AI"})
    assert response.status_code == 200
    json_data = response.get_json()
    assert "chat_id" in json_data
    assert "Ai generated reponse: Hello AI" in json_data["message"]

def test_404_error(client):
    response = client.get('/non-existent-route-xyz')
    assert response.status_code == 404