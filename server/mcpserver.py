from mcp.server.fastmcp import FastMCP

mcp = FastMCP("doctorserver")

doctors = {
    "DOC001": {
        "name": "Dr. Sarah Mitchell",
        "specialty": "Cardiology",
        "address": {
            "street": "1247 Medical Center Drive",
            "city": "Atlanta",
            "state": "GA",
            "zip_code": "30309",
        },
        "phone": "(404) 555-2847",
        "email": "s.mitchell@atlantaheart.com",
        "years_experience": 15,
        "board_certified": True,
        "hospital_affiliations": [
            "Emory University Hospital",
            "Piedmont Atlanta Hospital",
        ],
        "education": {
            "medical_school": "Duke University School of Medicine",
            "residency": "Johns Hopkins Hospital",
            "fellowship": "Cleveland Clinic",
        },
        "languages": ["English", "Spanish"],
        "accepts_new_patients": True,
        "insurance_accepted": [
            "Blue Cross Blue Shield",
            "Aetna",
            "Cigna",
            "UnitedHealth",
        ],
    },
    "DOC002": {
        "name": "Dr. James Rodriguez",
        "specialty": "Pediatrics",
        "address": {
            "street": "892 Children's Way, Suite 205",
            "city": "Phoenix",
            "state": "AZ",
            "zip_code": "85016",
        },
        "phone": "(602) 555-9134",
        "email": "j.rodriguez@phoenixpeds.com",
        "years_experience": 8,
        "board_certified": True,
        "hospital_affiliations": [
            "Phoenix Children's Hospital",
            "Banner Desert Medical Center",
        ],
        "education": {
            "medical_school": "University of Arizona College of Medicine",
            "residency": "Seattle Children's Hospital",
            "fellowship": None,
        },
        "languages": ["English", "Spanish"],
        "accepts_new_patients": True,
        "insurance_accepted": ["Medicaid", "CHIP", "Blue Cross Blue Shield", "Aetna"],
    },
    "DOC003": {
        "name": "Dr. Emily Chen",
        "specialty": "Dermatology",
        "address": {
            "street": "3401 Pacific Coast Highway",
            "city": "Los Angeles",
            "state": "CA",
            "zip_code": "90405",
        },
        "phone": "(310) 555-7623",
        "email": "e.chen@laskincare.com",
        "years_experience": 12,
        "board_certified": True,
        "hospital_affiliations": ["UCLA Medical Center", "Cedars-Sinai Medical Center"],
        "education": {
            "medical_school": "Stanford University School of Medicine",
            "residency": "UCSF Medical Center",
            "fellowship": "Memorial Sloan Kettering Cancer Center",
        },
        "languages": ["English", "Mandarin", "Cantonese"],
        "accepts_new_patients": False,
        "insurance_accepted": ["Blue Cross Blue Shield", "Cigna", "UnitedHealth"],
    },
    "DOC004": {
        "name": "Dr. Michael Thompson",
        "specialty": "Orthopedic Surgery",
        "address": {
            "street": "1156 Sports Medicine Plaza",
            "city": "Denver",
            "state": "CO",
            "zip_code": "80206",
        },
        "phone": "(303) 555-4892",
        "email": "m.thompson@denverortho.com",
        "years_experience": 22,
        "board_certified": True,
        "hospital_affiliations": [
            "National Jewish Health",
            "Presbyterian/Saint Joseph Hospital",
        ],
        "education": {
            "medical_school": "University of Colorado School of Medicine",
            "residency": "Mayo Clinic",
            "fellowship": "Hospital for Special Surgery",
        },
        "languages": ["English"],
        "accepts_new_patients": True,
        "insurance_accepted": [
            "Blue Cross Blue Shield",
            "Aetna",
            "Cigna",
            "Workers' Compensation",
        ],
    },
    "DOC005": {
        "name": "Dr. Priya Patel",
        "specialty": "Internal Medicine",
        "address": {
            "street": "2847 Medical Arts Building",
            "city": "Houston",
            "state": "TX",
            "zip_code": "77030",
        },
        "phone": "(713) 555-3651",
        "email": "p.patel@houstoninternal.com",
        "years_experience": 6,
        "board_certified": True,
        "hospital_affiliations": [
            "Houston Methodist Hospital",
            "MD Anderson Cancer Center",
        ],
        "education": {
            "medical_school": "Baylor College of Medicine",
            "residency": "Massachusetts General Hospital",
            "fellowship": None,
        },
        "languages": ["English", "Hindi", "Gujarati"],
        "accepts_new_patients": True,
        "insurance_accepted": [
            "Medicare",
            "Medicaid",
            "Blue Cross Blue Shield",
            "Humana",
        ],
    },
    "DOC006": {
        "name": "Dr. Robert Kim",
        "specialty": "Neurology",
        "address": {
            "street": "567 Brain & Spine Center",
            "city": "Seattle",
            "state": "WA",
            "zip_code": "98104",
        },
        "phone": "(206) 555-8274",
        "email": "r.kim@seattleneuro.com",
        "years_experience": 18,
        "board_certified": True,
        "hospital_affiliations": [
            "University of Washington Medical Center",
            "Swedish Medical Center",
        ],
        "education": {
            "medical_school": "University of Washington School of Medicine",
            "residency": "UCSF Medical Center",
            "fellowship": "Mayo Clinic",
        },
        "languages": ["English", "Korean"],
        "accepts_new_patients": False,
        "insurance_accepted": ["Blue Cross Blue Shield", "Aetna", "UnitedHealth"],
    },
    "DOC007": {
        "name": "Dr. Lisa Johnson",
        "specialty": "Obstetrics & Gynecology",
        "address": {
            "street": "4392 Women's Health Plaza, Floor 3",
            "city": "Miami",
            "state": "FL",
            "zip_code": "33156",
        },
        "phone": "(305) 555-1847",
        "email": "l.johnson@miamiwomenshealth.com",
        "years_experience": 14,
        "board_certified": True,
        "hospital_affiliations": [
            "Jackson Memorial Hospital",
            "Baptist Hospital of Miami",
        ],
        "education": {
            "medical_school": "University of Miami Miller School of Medicine",
            "residency": "New York-Presbyterian Hospital",
            "fellowship": "Brigham and Women's Hospital",
        },
        "languages": ["English", "Spanish", "French"],
        "accepts_new_patients": True,
        "insurance_accepted": ["Blue Cross Blue Shield", "Aetna", "Cigna", "Medicaid"],
    },
    "DOC008": {
        "name": "Dr. David Wilson",
        "specialty": "Emergency Medicine",
        "address": {
            "street": "789 Emergency Services Drive",
            "city": "Chicago",
            "state": "IL",
            "zip_code": "60611",
        },
        "phone": "(312) 555-9567",
        "email": "d.wilson@chicagoemergency.com",
        "years_experience": 11,
        "board_certified": True,
        "hospital_affiliations": [
            "Northwestern Memorial Hospital",
            "Rush University Medical Center",
        ],
        "education": {
            "medical_school": (
                "Northwestern University Feinberg School " "of Medicine"
            ),
            "residency": "Cook County Hospital",
            "fellowship": None,
        },
        "languages": ["English"],
        "accepts_new_patients": True,
        "insurance_accepted": ["All major insurances accepted", "Self-pay"],
    },
    "DOC009": {
        "name": "Dr. Amanda Foster",
        "specialty": "Psychiatry",
        "address": {
            "street": "1523 Mental Health Boulevard, Suite 401",
            "city": "Boston",
            "state": "MA",
            "zip_code": "02115",
        },
        "phone": "(617) 555-7412",
        "email": "a.foster@bostonpsych.com",
        "years_experience": 9,
        "board_certified": True,
        "hospital_affiliations": ["Massachusetts General Hospital", "McLean Hospital"],
        "education": {
            "medical_school": "Harvard Medical School",
            "residency": "Massachusetts General Hospital",
            "fellowship": "McLean Hospital",
        },
        "languages": ["English", "Portuguese"],
        "accepts_new_patients": True,
        "insurance_accepted": [
            "Blue Cross Blue Shield",
            "Harvard Pilgrim",
            "Tufts Health Plan",
        ],
    },
    "DOC010": {
        "name": "Dr. Christopher Lee",
        "specialty": "Oncology",
        "address": {
            "street": "2156 Cancer Treatment Center",
            "city": "Nashville",
            "state": "TN",
            "zip_code": "37232",
        },
        "phone": "(615) 555-6284",
        "email": "c.lee@nashvillecancer.com",
        "years_experience": 16,
        "board_certified": True,
        "hospital_affiliations": [
            "Vanderbilt University Medical Center",
            "Sarah Cannon Cancer Institute",
        ],
        "education": {
            "medical_school": "Vanderbilt University School of Medicine",
            "residency": "Memorial Sloan Kettering Cancer Center",
            "fellowship": "MD Anderson Cancer Center",
        },
        "languages": ["English"],
        "accepts_new_patients": False,
        "insurance_accepted": [
            "Blue Cross Blue Shield",
            "Cigna",
            "UnitedHealth",
            "Medicare",
        ],
    },
}


# Build server function
@mcp.tool()
def doctor_search(state: str) -> str:
    """This tool returns doctors that may be near you.
    Args:
        state: the two letter state code that you live in.
        Example payload: "CA"

    Returns:
        str: a list of doctors that may be near you
        Example Response "{"DOC001":{"name":"Dr John James",
        "specialty":"Cardiology"...}...}"
    """
    filtered_doctors = {
        doc_id: doc_info
        for doc_id, doc_info in doctors.items()
        if doc_info["address"]["state"] == state.upper()
    }
    return (
        str(filtered_doctors)
        if filtered_doctors
        else (f"No doctors found in state: {state}")
    )


# Kick off server if file is run
if __name__ == "__main__":
    import sys
    import os
    
    # Check if we should run in HTTP mode (for Docker container)
    if os.getenv("MCP_TRANSPORT") == "http":
        port = int(os.getenv("MCP_PORT", "8333"))
        print(f"Starting MCP server on HTTP port {port}")
        # Create a simple HTTP server using FastAPI
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        import uvicorn
        
        app = FastAPI(title="MCP Doctor Server")
        
        @app.post("/doctor_search")
        async def api_doctor_search(request: dict):
            state = request.get("state", "")
            result = doctor_search(state)
            return JSONResponse({"result": result})
        
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "MCP Doctor Server"}
        
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        print("Starting MCP server with stdio transport")
        mcp.run()
