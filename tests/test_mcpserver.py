"""Tests for the MCP server functionality with HTTP transport."""

import pytest
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from server.mcpserver import doctors, doctor_search, app


class TestMCPServer:
    """Test cases for MCP server functionality."""

    def test_doctors_data_structure(self):
        """Test that doctors data has the expected structure."""
        assert isinstance(doctors, dict)
        assert len(doctors) > 0
        
        # Test first doctor has required fields
        first_doctor = next(iter(doctors.values()))
        required_fields = [
            "name", "specialty", "address", "phone", "email",
            "years_experience", "board_certified", "hospital_affiliations"
        ]
        
        for field in required_fields:
            assert field in first_doctor, f"Missing required field: {field}"

    def test_doctor_search_by_state(self):
        """Test searching doctors by state."""
        # Test with known state
        ga_result = doctor_search("GA")
        assert isinstance(ga_result, str)
        assert "DOC001" in ga_result  # Dr. Sarah Mitchell is in GA
        assert "GA" in ga_result

    def test_doctor_search_case_insensitive(self):
        """Test that state search is case insensitive."""
        results_upper = doctor_search("GA")
        results_lower = doctor_search("ga")
        results_mixed = doctor_search("Ga")
        
        assert results_upper == results_lower == results_mixed

    def test_doctor_search_empty_state(self):
        """Test search with empty state."""
        result = doctor_search("")
        assert "No doctors found in state:" in result

    def test_doctor_search_nonexistent_state(self):
        """Test search with non-existent state returns no doctors message."""
        result = doctor_search("XY")  # Non-existent state
        assert "No doctors found in state: XY" in result

    def test_doctor_search_none_state(self):
        """Test search with None state."""
        # This will cause an AttributeError in the current implementation
        # We should handle this case properly
        with pytest.raises(AttributeError):
            doctor_search(None)

    def test_doctor_data_integrity(self):
        """Test that all doctors have valid data."""
        for doc_id, doctor in doctors.items():
            # Test required string fields are not empty
            assert doctor["name"].strip(), f"Doctor {doc_id} has empty name"
            assert doctor["specialty"].strip(), f"Doctor {doc_id} has empty specialty"
            assert doctor["phone"].strip(), f"Doctor {doc_id} has empty phone"
            assert doctor["email"].strip(), f"Doctor {doc_id} has empty email"
            
            # Test years_experience is positive
            assert doctor["years_experience"] > 0, f"Doctor {doc_id} has invalid experience"
            
            # Test address structure
            address = doctor["address"]
            assert "state" in address, f"Doctor {doc_id} missing state"
            assert "city" in address, f"Doctor {doc_id} missing city"
            assert len(address["state"]) == 2, f"Doctor {doc_id} has invalid state code"

    def test_doctor_specialties(self):
        """Test that doctors have valid specialties."""
        all_specialties = {doctor["specialty"] for doctor in doctors.values()}
        
        # Should have common medical specialties
        expected_specialties = {"Cardiology", "Pediatrics", "Dermatology"}
        found_specialties = all_specialties.intersection(expected_specialties)
        assert len(found_specialties) > 0, "Should have common medical specialties"

    def test_doctor_states_coverage(self):
        """Test that doctors are distributed across multiple states."""
        states = {doctor["address"]["state"] for doctor in doctors.values()}
        assert len(states) >= 3, "Should have doctors in multiple states"

    @pytest.mark.parametrize("state,expected_contains", [
        ("GA", "DOC001"),  # Dr. Sarah Mitchell
        ("CA", "DOC003"),  # Dr. Emily Chen
        ("TX", "DOC005"),  # Dr. Priya Patel
    ])
    def test_doctor_search_specific_states(self, state, expected_contains):
        """Test search for specific states."""
        result = doctor_search(state)
        assert isinstance(result, str)
        assert expected_contains in result


class TestDoctorDataModel:
    """Test cases for doctor data model validation."""

    def test_doctor_address_format(self):
        """Test that doctor addresses are properly formatted."""
        for doctor in doctors.values():
            address = doctor["address"]
            
            # Test required address fields
            assert "street" in address
            assert "city" in address
            assert "state" in address
            assert "zip_code" in address
            
            # Test state is 2-letter code
            assert len(address["state"]) == 2
            assert address["state"].isupper()

    def test_doctor_contact_info(self):
        """Test that doctor contact information is valid."""
        for doctor in doctors.values():
            # Test phone format (should contain digits)
            phone = doctor["phone"]
            assert any(c.isdigit() for c in phone), "Phone should contain digits"
            
            # Test email format (basic check)
            email = doctor["email"]
            assert "@" in email, "Email should contain @"
            assert "." in email, "Email should contain domain"

    def test_doctor_professional_info(self):
        """Test that doctor professional information is valid."""
        for doctor in doctors.values():
            # Test years_experience is reasonable
            years = doctor["years_experience"]
            assert 0 < years < 60, "Years of experience should be reasonable"
            
            # Test board_certified is boolean
            assert isinstance(doctor["board_certified"], bool)
            
            # Test hospital_affiliations is a list
            assert isinstance(doctor["hospital_affiliations"], list)
            assert len(doctor["hospital_affiliations"]) > 0

    def test_doctor_education_structure(self):
        """Test that doctor education information is properly structured."""
        for doctor in doctors.values():
            if "education" in doctor:
                education = doctor["education"]
                assert isinstance(education, dict)
                
                # Common education fields
                expected_fields = ["medical_school", "residency"]
                for field in expected_fields:
                    if field in education:
                        assert isinstance(education[field], (str, type(None)))


class TestMCPServerHTTP:
    """Test cases for MCP server HTTP transport functionality."""

    @pytest.fixture
    def client(self):
        """Create a test client for the MCP server app."""
        return TestClient(app)

    def test_mcp_server_index(self, client):
        """Test the MCP server index endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "doctor-search-server"
        assert data["version"] == "1.0.0"

    def test_mcp_list_tools(self, client):
        """Test the MCP list tools endpoint."""
        response = client.post("/", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "tools" in data["result"]
        
        tools = data["result"]["tools"]
        assert len(tools) > 0
        
        # Should have doctor_search tool
        tool_names = [tool["name"] for tool in tools]
        assert "doctor_search" in tool_names

    def test_mcp_call_tool_doctor_search(self, client):
        """Test calling the doctor_search tool via MCP."""
        response = client.post("/", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "doctor_search",
                "arguments": {"state": "GA"}
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "content" in data["result"]
        
        content = data["result"]["content"]
        assert len(content) > 0
        assert content[0]["type"] == "text"
        assert "DOC001" in content[0]["text"]  # Dr. Sarah Mitchell in GA

    def test_mcp_call_tool_invalid_state(self, client):
        """Test calling doctor_search with invalid state."""
        response = client.post("/", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "doctor_search",
                "arguments": {"state": "XY"}
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        content = data["result"]["content"]
        assert "No doctors found in state: XY" in content[0]["text"]

    def test_mcp_call_nonexistent_tool(self, client):
        """Test calling a non-existent tool."""
        response = client.post("/", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "nonexistent_tool",
                "arguments": {}
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32601  # Method not found

    def test_mcp_invalid_method(self, client):
        """Test calling an invalid MCP method."""
        response = client.post("/", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "invalid/method"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32601  # Method not found

    def test_mcp_malformed_request(self, client):
        """Test MCP server with malformed JSON-RPC request."""
        response = client.post("/", json={
            "invalid": "request"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32600  # Invalid Request


class TestMCPServerCurlCommands:
    """Test curl-equivalent commands for MCP server."""

    @pytest.fixture
    def client(self):
        """Create a test client for the MCP server app."""
        return TestClient(app)

    def test_curl_get_server_info(self, client):
        """
        Test equivalent of:
        curl -s http://localhost:8333/
        """
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "doctor-search-server"
        assert data["version"] == "1.0.0"

    def test_curl_list_mcp_tools(self, client):
        """
        Test equivalent of:
        curl -X POST http://localhost:8333/ \
             -H "Content-Type: application/json" \
             -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
        """
        response = client.post(
            "/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        
        tools = data["result"]["tools"]
        assert any(tool["name"] == "doctor_search" for tool in tools)

    def test_curl_search_doctors_georgia(self, client):
        """
        Test equivalent of:
        curl -X POST http://localhost:8333/ \
             -H "Content-Type: application/json" \
             -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "doctor_search", "arguments": {"state": "GA"}}}'
        """
        response = client.post(
            "/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "doctor_search",
                    "arguments": {"state": "GA"}
                }
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        
        content = data["result"]["content"]
        assert "Dr. Sarah Mitchell" in content[0]["text"]
        assert "Cardiology" in content[0]["text"]
        assert "Atlanta" in content[0]["text"]

    def test_curl_search_multiple_states(self, client):
        """
        Test searching multiple states with curl-equivalent commands.
        """
        test_states = ["CA", "TX", "FL", "NY"]
        
        for state in test_states:
            response = client.post(
                "/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "doctor_search",
                        "arguments": {"state": state}
                    }
                },
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            
            content = data["result"]["content"]
            # Either should find doctors or return "No doctors found"
            text_content = content[0]["text"]
            assert state in text_content or "No doctors found" in text_content

    def test_curl_verbose_request(self, client):
        """
        Test equivalent of:
        curl -v -X POST http://localhost:8333/ \
             -H "Content-Type: application/json" \
             -d '{"jsonrpc": "2.0", "id": 999, "method": "tools/call", "params": {"name": "doctor_search", "arguments": {"state": "CA"}}}'
        """
        response = client.post(
            "/",
            json={
                "jsonrpc": "2.0",
                "id": 999,
                "method": "tools/call",
                "params": {
                    "name": "doctor_search",
                    "arguments": {"state": "CA"}
                }
            },
            headers={"Content-Type": "application/json"}
        )
        
        # Verify response details (equivalent to verbose curl output)
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        assert response.elapsed_time is not None
        
        data = response.json()
        assert data["id"] == 999  # Should echo back the request ID
        assert "result" in data

    def test_curl_error_conditions(self, client):
        """
        Test various error conditions with curl-equivalent requests.
        """
        # Invalid JSON-RPC format
        response = client.post(
            "/",
            json={"invalid": "request"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32600  # Invalid Request

        # Invalid tool name
        response = client.post(
            "/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "invalid_tool",
                    "arguments": {}
                }
            },
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32601  # Method not found

    def test_curl_health_check(self, client):
        """
        Test health check endpoint:
        curl -s http://localhost:8333/health
        """
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
