from enum import Enum

class PlanetAttributeType(Enum):
        COLOR = "color"
        DIRECTION = "direction"
        NONE = None

class Color(Enum):
        BLUE = "blue"
        RED = "red"
        PURPLE = "purple"
        WHITE = "white"

class Direction(Enum):
        UP = "up"
        DOWN = "down"
        RIGHT = "right"
        LEFT = "left"
class Planet(Enum): 

    SOLOON = {
        "attribute_type": PlanetAttributeType.COLOR,
        "attribute_values": set(Color),
        "is_planet": True
    }
    COMETH = {
        "attribute_type": PlanetAttributeType.DIRECTION,
        "atribute_values": set(Direction),
        "is_planet": True
    }
    POLYANET = {
        "attribute_type": PlanetAttributeType.NONE,
        "attribute_values": None,
        "is_planet": True
    }
    SPACE = {
        "attribute_type": PlanetAttributeType.NONE,
        "attribute_values": None,
        "is_planet": False
    }

    def validate_attribute(self, attribute):
        if self.value["attribute_type"] == "direction":
            if attribute not in self.value["attribute_value"]:
                raise ValueError(f'{attribute} is not a valid direction')
        elif self.value["attribute_type"] == "color":
            if attribute not in self.value["attribute_value"]: 
                raise ValueError(f'{attribute} is not a valid color')
        elif self.value["attribute_type"] == None:
            if attribute is not None:
                raise ValueError(f'{attribute} is not a valid attribute')
        return True
