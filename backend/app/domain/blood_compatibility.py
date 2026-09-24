from app.models.inventory import BloodGroup, BloodComponent
from typing import List

# Standard Donor to Recipient compatibility rules
# Key is Recipient, Values are Compatible Donors
_RBC_COMPATIBILITY = {
    BloodGroup.O_NEG: [BloodGroup.O_NEG],
    BloodGroup.O_POS: [BloodGroup.O_NEG, BloodGroup.O_POS],
    BloodGroup.A_NEG: [BloodGroup.O_NEG, BloodGroup.A_NEG],
    BloodGroup.A_POS: [BloodGroup.O_NEG, BloodGroup.O_POS, BloodGroup.A_NEG, BloodGroup.A_POS],
    BloodGroup.B_NEG: [BloodGroup.O_NEG, BloodGroup.B_NEG],
    BloodGroup.B_POS: [BloodGroup.O_NEG, BloodGroup.O_POS, BloodGroup.B_NEG, BloodGroup.B_POS],
    BloodGroup.AB_NEG: [BloodGroup.O_NEG, BloodGroup.A_NEG, BloodGroup.B_NEG, BloodGroup.AB_NEG],
    BloodGroup.AB_POS: [
        BloodGroup.O_NEG, BloodGroup.O_POS, BloodGroup.A_NEG, BloodGroup.A_POS,
        BloodGroup.B_NEG, BloodGroup.B_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS
    ],
}

# Plasma is the reverse of RBC for ABO, Rh is usually not an issue but we match strictly or conservatively
_PLASMA_COMPATIBILITY = {
    BloodGroup.O_NEG: [BloodGroup.O_NEG, BloodGroup.O_POS, BloodGroup.A_NEG, BloodGroup.A_POS, BloodGroup.B_NEG, BloodGroup.B_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.O_POS: [BloodGroup.O_NEG, BloodGroup.O_POS, BloodGroup.A_NEG, BloodGroup.A_POS, BloodGroup.B_NEG, BloodGroup.B_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.A_NEG: [BloodGroup.A_NEG, BloodGroup.A_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.A_POS: [BloodGroup.A_NEG, BloodGroup.A_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.B_NEG: [BloodGroup.B_NEG, BloodGroup.B_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.B_POS: [BloodGroup.B_NEG, BloodGroup.B_POS, BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.AB_NEG: [BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.AB_POS: [BloodGroup.AB_NEG, BloodGroup.AB_POS],
}

# Platelets generally follow RBC rules for ABO when suspended in plasma, though rules can be looser in emergency
_PLATELET_COMPATIBILITY = _RBC_COMPATIBILITY

# Whole blood requires exact ABO/Rh match
_WHOLE_BLOOD_COMPATIBILITY = {bg: [bg] for bg in BloodGroup}


def get_compatible_donors(recipient_group: BloodGroup, component: BloodComponent) -> List[BloodGroup]:
    """Returns a list of compatible donor blood groups for a given recipient and component."""
    if component == BloodComponent.RBC:
        return _RBC_COMPATIBILITY.get(recipient_group, [])
    elif component == BloodComponent.PLASMA:
        return _PLASMA_COMPATIBILITY.get(recipient_group, [])
    elif component == BloodComponent.PLATELETS:
        return _PLATELET_COMPATIBILITY.get(recipient_group, [])
    elif component == BloodComponent.WHOLE_BLOOD:
        return _WHOLE_BLOOD_COMPATIBILITY.get(recipient_group, [])
    elif component == BloodComponent.CRYOPRECIPITATE:
        return [bg for bg in BloodGroup] # Any blood group
    return []

def is_compatible(donor_group: BloodGroup, recipient_group: BloodGroup, component: BloodComponent) -> bool:
    """Checks if a donor blood group is compatible with a recipient for a specific component."""
    compatible_donors = get_compatible_donors(recipient_group, component)
    return donor_group in compatible_donors

def get_emergency_universal_donor(component: BloodComponent) -> BloodGroup:
    """Returns the universal donor blood group for emergency use based on component."""
    if component == BloodComponent.RBC or component == BloodComponent.WHOLE_BLOOD:
        return BloodGroup.O_NEG
    elif component == BloodComponent.PLASMA or component == BloodComponent.PLATELETS:
        return BloodGroup.AB_POS # AB Plasma is universal
    return BloodGroup.O_NEG
