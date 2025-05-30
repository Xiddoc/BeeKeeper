from beekeeper import Exemption, Location, Rank


class McDonaldsExemption(Exemption):
    STANDING = "STANDING"
    ALLERGIES = "ALLERGIES"
    EXPOSURE_TO_HEAT = "EXPOSURE_TO_HEAT"


class McDonaldsRank(Rank):
    WORKER = "WORKER"
    MANAGER = "MANAGER"
    SUPERVISOR = "SUPERVISOR"


class McDonaldsLocation(Location):
    HERZLIYA = "HERZLIYA"
    TEL_AVIV = "TEL_AVIV"
    KFAR_SABA = "KFAR_SABA"
