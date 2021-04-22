from walletv2 import Wallet


class WalletNode:
    """
    This wallet node class runs a wallet instance
    """

    def __init__(self):
        self.wallet = Wallet()

    # Prompts the user for its choice and return it
    def get_user_choice(self):
        user_input = input("Your choice: ")
        return user_input

    # Starts the node and waits for user input
    def listen_for_input(self) -> None:
        waiting_for_input = True

        # User Input Interface
        while waiting_for_input:
            print("Please choose")
            print("1: Create wallet")
            print("2: Load wallet")
            print("3: Create address")
            print("q: Quit")
            user_choice = self.get_user_choice()
            if user_choice == "1":
                private_key, _public_key = self.wallet.generate_keys()
                self.wallet.save_keys(private_key)
                print("Wallet created")
            elif user_choice == "2":
                self.wallet.retreive_keys()
                print("Wallet keys loaded")
            elif user_choice == "3":
                address = self.wallet.generate_address()
                self.wallet.save_address(address)
                print("Address created and saved")
            elif user_choice == "q":
                waiting_for_input = False
            else:
                break
            print(
                "Wallet Address: {}\nBalance: {:6.2f}".format(self.wallet.address, 0.0)
            )
        else:
            print("User left!")

        print("Done!")


if __name__ == "__main__":
    node = WalletNode()
    node.listen_for_input()
