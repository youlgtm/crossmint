from planet.planet_definitions import Planet, Color, Direction, PlanetAttributeType
import hashlib
import json
import logging 

logger = logging.getLogger(__name__)

class MapProcessor: 
    def __init__(self, request_instance):
        self.goal_map = request_instance.get_map("goal.json", "goal_map", "server")
        self.current_map = request_instance.get_map("current.json", "current_map", "server")
        self.candidate_id = request_instance.candidate_id
        self.request_instance = request_instance
        self.mismatches = []

    def get_request_payload(self, operation):
        payload_list = []
        if(operation == "delete"):
            map_dictionary = self.current_map_dict_without_attributes()
        elif(operation == "retry"):
            map_dictionary = self.mismatches
        else:
            map_dictionary = self.goal_map_dict()

        for element in map_dictionary:
            if(operation == "retry"):
                print(element)
            planet = Planet[element["planet"].upper()]
            if planet == Planet.SPACE:
                continue
             
            payload = {
                "name": element["planet"].lower(),
                "data": {
                    "candidateId": self.candidate_id,
                    "row": element["row"],
                    "column": element["col"]
                }
            }
            
            attribute_type = element.get("attribute_type") 
            attribute = element.get("attribute")

            if attribute_type and planet.validate_attribute(attribute):
                payload["data"][element["attribute_type"].lower()] = element["attribute"].lower()

            payload_list.append(payload) 

        return payload_list


    # Function to flatten map into a dict, ready for POST requests, ideal for goal Megaverse
    def goal_map_dict(self):
        map_dictionary =  [{"planet": planet, "attribute_type": attribute_type, "attribute": attribute, "row": row_index, "col": col_index} 
                for row_index, row in enumerate(self.goal_map) 
                for col_index, element in enumerate(row) 
                for planet, attribute_type, attribute in [self.split_planet_property(element)]]
        return map_dictionary

    # Function to flatten map into a dict, ready for DELETE requests, ideal for map cleanup
    def current_map_dict_without_attributes(self):
        map_dictionary = [{"planet": planet.lower(), "row": row_index, "col": col_index}
                          for row_index, row in enumerate(self.current_map)
                          for col_index, element in enumerate(row)
                          for planet, _, _ in [self.find_planets(element)]
                          if "space" not in planet]
        return map_dictionary
    
    # Function to split goal map instruction of planet attribute type (color, direction, none) and planet value (red, left)
    def split_planet_property(self, element):
        underscore_index = element.find("_")
        if(underscore_index != -1):
            planet_name = element[underscore_index + 1: len(element)]
            if(Planet[planet_name].validate_attribute(element[0: underscore_index])):
                attribute = element[0: underscore_index]
                attribute_type = Planet[planet_name].value["attribute_type"].value
            else:
                logger.warning("Wrong attributes for the planet")
        else:
            planet_name = element 
            attribute = None
            attribute_type = Planet[element].value["attribute_type"].value

        return planet_name, attribute_type, attribute

    # Function to match planets and their types
    def find_planets(self, element):
        if(element):
            planet_type = element["type"]
            if(planet_type == 0):
                return "POLYANET", None, None
            elif(planet_type == 1):
                return "SOLOON", "color", element["color"].upper()
            elif(planet_type == 2):
                return "COMETH", "direction", element["direction"].upper()
            else:
                raise ValueError(f"Unknown planet type: {planet_type}")
        else:
            return "SPACE", None, None

    def hash_list(self, lst):
        list_string = json.dumps(lst)
        sha1 = hashlib.sha1()
        sha1.update(list_string.encode('utf-8'))
        return sha1.hexdigest()


    def current_map_dict_with_attributes(self):
        map_dictionary = [{"planet": planet, "attribute_type": attribute_type, "attribute": attribute, "row": row_index, "col": col_index}
                          for row_index, row in enumerate(self.current_map)
                          for col_index, element in enumerate(row)
                          for planet, attribute_type, attribute in [self.find_planets(element)]]
        return map_dictionary

    def validate_map(self, validation_type):
        if(validation_type == "empty"):
            goal_map_dict = [{"planet": "SPACE", "attribute_type": None, "attribute": None, "row": row_index, "col": col_index}
                                for row_index, row in enumerate(self.current_map)
                                for col_index, _ in enumerate(row)]
        elif(validation_type == "goal"):
            goal_map_dict = self.goal_map_dict()

        self.current_map = self.request_instance.get_map("current.json", "current_map", "server")
        current_map_dict = self.current_map_dict_with_attributes()

        hash_current = self.hash_list(current_map_dict)
        hash_goal = self.hash_list(goal_map_dict)
        logger.info(f'current_map SHA-1 HASH: {hash_current}')
        logger.info(f'{validation_type}_map SHA-1 HASH: {hash_goal}')

        if(hash_goal == hash_current):
            return True, self.mismatches 
        else:
            goal_map_mapping = {(d['row'], d['col']): d for d in goal_map_dict}

            for val in current_map_dict:
                key = (val['row'], val['col'])
                if key in goal_map_mapping:
                    target = goal_map_mapping[key]
                    
                    if(target != val):
                        self.mismatches.append(target) 
            return False, self.mismatches

