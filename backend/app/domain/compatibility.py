from typing import List

class BloodGroup:
    O_NEG = "O-"
    O_POS = "O+"
    A_NEG = "A-"
    A_POS = "A+"
    B_NEG = "B-"
    B_POS = "B+"
    AB_NEG = "AB-"
    AB_POS = "AB+"

class ComponentType:
    WHOLE_BLOOD = "WHOLE_BLOOD"
    RBC = "RBC"
    PLASMA = "PLASMA"
    PLATELETS = "PLATELETS"
    CRYOPRECIPITATE = "CRYOPRECIPITATE"

# Compatibility maps defined as: {Recipient: [Allowed Donors]}
RBC_COMPATIBILITY = {
    BloodGroup.O_NEG: [BloodGroup.O_NEG],
    BloodGroup.O_POS: [BloodGroup.O_NEG, BloodGroup.O_POS],
    BloodGroup.A_NEG: [BloodGroup.O_NEG, BloodGroup.A_NEG],
    BloodGroup.A_POS: [BloodGroup.O_NEG, BloodGroup.O_POS, BloodGroup.A_NEG, BloodGroup.A_POS],
    BloodGroup.B_NEG: [BloodGroup.O_NEG, BloodGroup.B_NEG],
    BloodGroup.B_POS: [BloodGroup.O_NEG, BloodGroup.O_POS, BloodGroup.B_NEG, BloodGroup.B_POS],
    BloodGroup.AB_NEG: [BloodGroup.O_NEG, BloodGroup.A_NEG, BloodGroup.B_NEG, BloodGroup.AB_NEG],
    BloodGroup.AB_POS: [BloodGroup.O_NEG, BloodGroup.O_POS, BloodGroup.A_NEG, BloodGroup.A_POS, 
                        BloodGroup.B_NEG, BloodGroup.B_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS],
}

# Plasma rules are reversed from RBC regarding ABO, Rh is usually ignored but we'll include it.
PLASMA_COMPATIBILITY = {
    BloodGroup.O_NEG: [BloodGroup.O_NEG, BloodGroup.O_POS, BloodGroup.A_NEG, BloodGroup.A_POS, 
                       BloodGroup.B_NEG, BloodGroup.B_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.O_POS: [BloodGroup.O_NEG, BloodGroup.O_POS, BloodGroup.A_NEG, BloodGroup.A_POS, 
                       BloodGroup.B_NEG, BloodGroup.B_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.A_NEG: [BloodGroup.A_NEG, BloodGroup.A_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.A_POS: [BloodGroup.A_NEG, BloodGroup.A_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.B_NEG: [BloodGroup.B_NEG, BloodGroup.B_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.B_POS: [BloodGroup.B_NEG, BloodGroup.B_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.AB_NEG: [BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.AB_POS: [BloodGroup.AB_NEG, BloodGroup.AB_POS],
}

def get_compatible_donors(recipient_group: str, component_type: str) -> List[str]:
    """
    Returns a list of blood groups that can safely donate to the recipient for the given component.
    """
    if component_type in [ComponentType.RBC, ComponentType.WHOLE_BLOOD, ComponentType.PLATELETS]:
        return RBC_COMPATIBILITY.get(recipient_group, [])
    elif component_type == ComponentType.PLASMA:
        return PLASMA_COMPATIBILITY.get(recipient_group, [])
    elif component_type == ComponentType.CRYOPRECIPITATE:
        # Cryo is generally universally compatible
        return [BloodGroup.O_NEG, BloodGroup.O_POS, BloodGroup.A_NEG, BloodGroup.A_POS,
                BloodGroup.B_NEG, BloodGroup.B_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS]
    return []

def is_compatible(donor_group: str, recipient_group: str, component_type: str) -> bool:
    """
    Checks if a donor blood group is compatible with a recipient for a specific component.
    """
    compatible_donors = get_compatible_donors(recipient_group, component_type)
    return donor_group in compatible_donors
