

class Student:
    def __init__(self, name, house):
        if not name:
            raise ValueError("Missing name")
        self.name=name
        self.house=house
   
    
    def __str__(self):
        return f"{self.name} from {self.house}"
    
    #Getter
    @property
    def house(self):
        return self._house
    
    # Setter
    @house.setter
    def house(self, house):
        if house not in ["Gryffindor", "Hufflepuff", "Ravenclaw", "Slytherin"]:
            raise ValueError("Invalid house")
        self._house=house
        

def main():
    student= get_student()
    student.house= "Number four"
    print(student)

def get_student():
    name= input("Name: ")
    house= input("House: ")
    return Student(name, house)

class Dog:

    def __init__(self, name, color):
        self.name=name
        self.color=color

    
if __name__ == "__main__":
    dog1 = Dog("Happy", "Black")
    dog2 = Dog("Polo", "Yellow")
    print(dog1.name)
    pass