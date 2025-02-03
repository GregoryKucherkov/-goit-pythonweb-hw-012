from datetime import date


test_contact = {
    "name": "test_contact",
    "lastname": "test_last",
    "email": "test@gmail.com",
    "phone": "096-123-45-67",
    "birthdate": date(2011, 12, 12).isoformat(),
    # "birthdate": str(date(2001, 12, 12)),
    "notes": "some_note",
}


def test_create_contact(client, get_token):
    response = client.post(
        "/api/contacts",
        json=test_contact,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == test_contact["name"]
    assert "id" in data
    assert "phone" in data


def test_get_contact(client, get_token):
    response = client.get(
        "/api/contact/1", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == test_contact["name"]
    assert "id" in data


def test_get_contact_not_found(client, get_token):
    response = client.get(
        "/api/contact/2", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"


def test_get_contacts(client, get_token):
    response = client.get(
        "/api/contacts", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["name"] == test_contact["name"]
    assert "id" in data[0]
    assert len(data) > 0


def test_update_contact(client, get_token):
    updated_test_contact = test_contact.copy()
    updated_test_contact["name"] = "New_name"

    response = client.put(
        "/api/contact/1",
        json=updated_test_contact,
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == updated_test_contact["name"]
    assert "id" in data
    assert data["id"] == 1


def test_update_contact_not_found(client, get_token):
    updated_test_contact = test_contact.copy()
    updated_test_contact["name"] = "New_name"

    response = client.put(
        "/api/contact/2",
        json=updated_test_contact,
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"


def test_delete_contact(client, get_token):
    response = client.delete(
        "/api/contact/1", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.text
    assert data == ""


def test_repeat_delete_contact(client, get_token):
    response = client.delete(
        "/api/contacts/1", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"
