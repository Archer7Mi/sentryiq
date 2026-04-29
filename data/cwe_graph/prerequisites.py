"""CWE prerequisite graph.

Represents prerequisite relationships between CWE weaknesses.
Format: { "CWE-A": ["CWE-B", "CWE-C"], ... }
Meaning: CWE-A enables/amplifies CWE-B and CWE-C (if both exist in a stack, 
they form a more severe chain).

This is a representative subset. Production would ingest the full MITRE CWE 
ontology.
"""

CWE_PREREQUISITES = {
    # Web vulnerabilities leading to higher-impact outcomes
    "CWE-79": ["CWE-200", "CWE-434"],  # XSS enables Information Disclosure & File Upload
    "CWE-89": ["CWE-200", "CWE-434", "CWE-427"],  # SQL Injection enables disc/upload/code execution
    "CWE-78": ["CWE-200", "CWE-427"],  # OS Command Injection enables disc/code execution
    "CWE-200": ["CWE-434", "CWE-427"],  # Information Disclosure enables upload/code execution
    "CWE-434": ["CWE-427"],  # Unrestricted File Upload enables Code Execution
    "CWE-427": ["CWE-94"],  # Code Execution enables Code Injection
    "CWE-94": ["CWE-269"],  # Code Injection enables Privilege Escalation
    
    # Authentication/Session vulnerabilities
    "CWE-287": ["CWE-384"],  # Improper Auth enables Session Fixation
    "CWE-384": ["CWE-427"],  # Session Fixation enables Code Execution
    "CWE-613": ["CWE-287"],  # Insufficient Session Expiration enables Auth Bypass
    
    # Memory corruption leading to privilege escalation
    "CWE-120": ["CWE-269"],  # Buffer Overflow enables Privilege Escalation
    "CWE-416": ["CWE-269"],  # Use-After-Free enables Privilege Escalation
    "CWE-122": ["CWE-269"],  # Heap-based Buffer Overflow enables Privesc
    
    # Privilege escalation leading to system compromise
    "CWE-269": ["CWE-276"],  # Privesc enables Improper Access Control
    "CWE-276": ["CWE-427"],  # Improper Access Control enables Code Execution
    
    # Network/protocols
    "CWE-295": ["CWE-311"],  # Improper Cert Validation enables Cleartext Transmission
    "CWE-311": ["CWE-200"],  # Cleartext Transmission enables Information Disclosure
    
    # Cryptography
    "CWE-326": ["CWE-311"],  # Inadequate Encryption enables Cleartext Transmission
    "CWE-327": ["CWE-200"],  # Weak Crypto enables Information Disclosure
}


def get_prerequisites(cwe_id: str) -> list[str]:
    """Get list of CWEs that this CWE can lead to.
    
    Args:
        cwe_id: CWE identifier (e.g., "CWE-79")
        
    Returns:
        List of CWE IDs that can be enabled/amplified by this CWE.
    """
    return CWE_PREREQUISITES.get(cwe_id, [])


def get_prerequisite_for(cwe_id: str) -> list[str]:
    """Get list of CWEs that can lead to this CWE (reverse lookup).
    
    Args:
        cwe_id: CWE identifier
        
    Returns:
        List of CWE IDs that enable this one.
    """
    result = []
    for source, targets in CWE_PREREQUISITES.items():
        if cwe_id in targets:
            result.append(source)
    return result
