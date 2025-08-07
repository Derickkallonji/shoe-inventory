# inventory.py
import os

class Shoe:
    def __init__(self, country, code, product, cost, quantity):
        self.country = country
        self.code = code
        self.product = product
        self.cost = float(cost)
        self.quantity = int(quantity)

    def get_cost(self):
        return self.cost

    def get_quantity(self):
        return self.quantity

    def __str__(self):
        return f"{self.country},{self.code},{self.product},{self.cost},{self.quantity}"

shoe_list = []

def check_empty_inventory():
    """Helper function to check if inventory is empty."""
    if not shoe_list:
        print("No shoes in inventory!")
        return True
    return False

def read_shoes_data():
    """Read shoe data from inventory.txt and populate shoe_list."""
    try:
        with open('inventory.txt', 'r') as file:
            lines = file.readlines()
            if len(lines) == 0:  # Empty file
                with open('inventory.txt', 'w') as f:
                    f.write("Country,Code,Product,Cost,Quantity\n")
                print("Created new inventory.txt file!")
                return
            if len(lines) == 1:  # Only header
                print("Inventory file contains only header!")
                return
            for line in lines[1:]:  # Skip header
                data = line.strip().split(',')
                if len(data) != 5:
                    print(f"Skipping invalid line: {line.strip()}")
                    continue
                try:
                    country, code, product, cost, quantity = data
                    float(cost)  # Validate cost
                    int(quantity)  # Validate quantity
                    shoe = Shoe(country, code, product, cost, quantity)
                    shoe_list.append(shoe)
                except ValueError:
                    print(f"Skipping invalid data in line: {line.strip()}")
        print("Inventory data loaded successfully!")
    except FileNotFoundError:
        with open('inventory.txt', 'w') as file:
            file.write("Country,Code,Product,Cost,Quantity\n")
        print("Created new inventory.txt file!")
    except Exception as e:
        print(f"An error occurred: {e}")

def capture_shoes():
    """Capture new shoe details and add to inventory."""
    country = input("Enter country: ").strip()
    if not country:
        print("Country cannot be empty!")
        return
    code = input("Enter shoe code: ").strip()
    if not code:
        print("Code cannot be empty!")
        return
    product = input("Enter product name: ").strip()
    if not product:
        print("Product name cannot be empty!")
        return
    while True:
        try:
            cost = float(input("Enter cost: "))
            quantity = int(input("Enter quantity: "))
            if cost < 0 or quantity < 0:
                print("Cost and quantity cannot be negative!")
                continue
            break
        except ValueError:
            print("Please enter valid numeric values for cost and quantity!")
    
    new_shoe = Shoe(country, code, product, cost, quantity)
    shoe_list.append(new_shoe)
    try:
        with open('inventory.txt', 'a') as file:
            file.write(str(new_shoe) + '\n')
        print("Shoe added successfully!")
    except Exception as e:
        print(f"Error saving to file: {e}")

def view_all():
    """Display all shoes in a formatted table."""
    if check_empty_inventory():
        return
    
    print("\nInventory List:")
    print("-" * 70)
    print(f"{'Country':<15} {'Code':<10} {'Product':<20} {'Cost':<10} {'Quantity':<10}")
    print("-" * 70)
    for shoe in shoe_list:
        print(f"{shoe.country:<15} {shoe.code:<10} {shoe.product:<20} {shoe.cost:<10.2f} {shoe.quantity:<10}")
    print("-" * 70)

def re_stock():
    """Restock the shoe with the lowest quantity."""
    if check_empty_inventory():
        return
    
    min_shoe = min(shoe_list, key=lambda x: x.quantity)
    print(f"\nShoe with lowest quantity:\n{min_shoe}")
    
    try:
        choice = input("Would you like to restock this shoe? (yes/no): ").lower()
        if choice == 'yes':
            additional = int(input("Enter quantity to add: "))
            if additional < 0:
                print("Quantity to add cannot be negative!")
                return
            min_shoe.quantity += additional
            
            with open('inventory.txt', 'w') as file:
                file.write("Country,Code,Product,Cost,Quantity\n")
                for shoe in shoe_list:
                    file.write(str(shoe) + '\n')
            
            print("Stock updated successfully!")
    except ValueError:
        print("Please enter a valid number!")
    except Exception as e:
        print(f"An error occurred: {e}")

def search_shoe():
    """Search for a shoe by code."""
    if check_empty_inventory():
        return
    
    code = input("Enter shoe code to search: ").strip()
    if not code:
        print("Code cannot be empty!")
        return
    for shoe in shoe_list:
        if shoe.code == code:
            print(f"\nFound shoe:\n{shoe}")
            return
    print("Shoe not found!")

def value_per_item():
    """Calculate and display total value per shoe."""
    if check_empty_inventory():
        return
    
    print("\nValue per item:")
    print("-" * 50)
    print(f"{'Product':<20} {'Value':<10}")
    print("-" * 50)
    for shoe in shoe_list:
        value = shoe.cost * shoe.quantity
        print(f"{shoe.product:<20} {value:<10.2f}")
    print("-" * 50)

def highest_qty():
    """Display the shoe with the highest quantity."""
    if check_empty_inventory():
        return
    
    max_shoe = max(shoe_list, key=lambda x: x.quantity)
    print(f"\nShoe with highest quantity (For Sale):\n{max_shoe}")

def main():
    """Main menu-driven interface."""
    read_shoes_data()
    
    while True:
        # Clear screen for better UX
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n=== Shoe Inventory Management System ===")
        print("1. Add new shoe")
        print("2. View all shoes")
        print("3. Restock shoes")
        print("4. Search shoe")
        print("5. Calculate value per item")
        print("6. View shoe with highest quantity")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            capture_shoes()
        elif choice == '2':
            view_all()
        elif choice == '3':
            re_stock()
        elif choice == '4':
            search_shoe()
        elif choice == '5':
            value_per_item()
        elif choice == '6':
            highest_qty()
        elif choice == '7':
            print("Thank you for using the Shoe Inventory System!")
            break
        else:
            print("Invalid choice! Please try again.")
        input("\nPress Enter to continue...")  # Pause for readability

if __name__ == "__main__":
    main()