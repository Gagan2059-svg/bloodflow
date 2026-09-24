from app.domain.compatibility import get_compatible_donors, is_compatible, ComponentType

def test_is_compatible():
    c_type = ComponentType.RBC
    
    # Identical types
    assert is_compatible("O+", "O+", c_type) is True
    assert is_compatible("AB-", "AB-", c_type) is True
    
    # Universal donor (O-)
    assert is_compatible("O-", "A+", c_type) is True
    assert is_compatible("O-", "AB+", c_type) is True
    
    # Universal recipient (AB+)
    assert is_compatible("O-", "AB+", c_type) is True
    assert is_compatible("A+", "AB+", c_type) is True
    assert is_compatible("B-", "AB+", c_type) is True
    
    # Incompatible Rh
    assert is_compatible("A+", "A-", c_type) is False
    assert is_compatible("O+", "O-", c_type) is False
    
    # Incompatible ABO
    assert is_compatible("A+", "B+", c_type) is False
    assert is_compatible("AB+", "O+", c_type) is False

def test_get_compatible_donors():
    c_type = ComponentType.RBC
    
    # O- can only receive O-
    assert set(get_compatible_donors("O-", c_type)) == {"O-"}
    
    # A+ can receive A+, A-, O+, O-
    assert set(get_compatible_donors("A+", c_type)) == {"A+", "A-", "O+", "O-"}
    
    # AB+ can receive all
    assert len(get_compatible_donors("AB+", c_type)) == 8
