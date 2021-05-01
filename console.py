import logging
import sys
import json

from uuid import uuid4

from PyQt5.QtCore import QRunnable, Qt, QThreadPool
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QGridLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QWidget,
)

from blockchain import Blockchain
from transaction import Transaction
from walletv2 import Wallet

logging.basicConfig(level=logging.INFO)


# 1. Subclass QRunnable
class Register(QRunnable):
    def __init__(self, blockchain, statusBar):
        super().__init__()
        self.blockchain = blockchain
        self.statusBar = statusBar

    def run(self):
        # Your long-running task goes here ...
        self.statusBar().showMessage("Registering to masternode....")
        self.blockchain.register_node("https://sedrik.life/blockchain")
        self.statusBar().showMessage("Registered")


# 1. Subclass QRunnable
class Sync(QRunnable):
    def __init__(self, blockchain, wallet, label, statusBar):
        super().__init__()
        self.blockchain = blockchain
        self.wallet = wallet
        self.statusBar = statusBar
        self.label = label

    def run(self):
        # Your long-running task goes here ...
        self.statusBar().showMessage("Syncing with masternode....")
        self.blockchain.resolve_conflicts()
        self.statusBar().showMessage(
            f"Synced {self.blockchain.chain_length} blocks with masternode"
        )
        self.label.setText(
            f"Address: {self.wallet.address}\nBalance: {self.blockchain.get_balance()}"
        )


# 1. Subclass QRunnable
class MineBlock(QRunnable):
    def __init__(self, blockchain, wallet, statusBar, label):
        super().__init__()
        self.blockchain = blockchain
        self.wallet = wallet
        self.statusBar = statusBar
        self.label = label

    def run(self):
        # Your long-running task goes here ...
        self.statusBar().showMessage("Mining new block....")
        self.blockchain.mine_block()
        self.label.setText(
            "Address: {}\nBalance: {}".format(
                self.wallet.address, self.blockchain.get_balance()
            )
        )
        self.statusBar().showMessage("Block Mined!")


class TransactionWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = self.parent()
        self.blockchain = self.parent.blockchain
        self.wallet = self.parent.wallet

        self.recipient = QLineEdit()
        self.amount = QLineEdit()
        self.button = QPushButton("Submit Transaction")
        self.button.clicked.connect(self.submit_transaction)

        layout = QGridLayout()

        layout.addWidget(QLabel("Recipient: "), 1, 0)
        layout.addWidget(self.recipient, 1, 1)
        layout.addWidget(QLabel("Amount: "), 2, 0)
        layout.addWidget(self.amount, 2, 1)
        layout.addWidget(self.button, 3, 0)
        self.setLayout(layout)
        self.setFixedWidth(self.parent.width())

    def submit_transaction(self):
        signature = self.wallet.sign_transaction(
            self.wallet.address, self.recipient.text(), self.amount.text()
        )
        transaction = Transaction(
            sender=self.wallet.address,
            recipient=self.recipient.text(),
            amount=self.amount.text(),
            signature=signature,
        )
        if self.blockchain.add_transaction(transaction):
            logging.info("Added transaction!")
            self.deleteLater()
        else:
            logging.info("Transaction failed!")


class WalletWidget(QWidget):
    def __init__(self, parent, action):
        super().__init__(parent)
        self.parent = self.parent()
        self.node_id = self.parent.node_id
        self.action = action

        layout = QGridLayout()

        if self.action == "logout":
            self.parent.wallet = Wallet()
            self.parent.label.setText("")
            self.deleteLater()

        self.password = QInputDialog()
        self.password.setTextEchoMode(2)
        self.password.accepted.connect(self.wallet_action)

        layout.addWidget(self.password, 1, 0)
        self.setLayout(layout)
        self.setFixedWidth(self.parent.width())

    def wallet_action(self) -> None:
        result = False
        if self.action == "create":
            result = self.parent.wallet.create_login(self.password.textValue())
        elif self.action == "login":
            result = self.parent.wallet.login(self.password.textValue())

        if result:
            self.parent.blockchain = Blockchain(
                self.parent.wallet.address, self.node_id
            )
            self.parent.registerNode()
            self.parent.syncNode()
        self.deleteLater()


class Window(
    QMainWindow
):  # pylint: disable=too-many-instance-attributes,too-many-locals,too-many-statements
    def __init__(self):
        super().__init__()
        self.node_id = str(uuid4())
        self.blockchain = Blockchain("", self.node_id)
        self.wallet = Wallet()
        self.threadCount = QThreadPool.globalInstance().maxThreadCount()
        self.pool = QThreadPool.globalInstance()

        self.setupUi()
        self.registerNode()
        self.syncNode()

    def __add_wallet_widget(self, action) -> None:
        self.grid.addWidget(WalletWidget(self, action))

    def __add_transaction_widget(self) -> None:
        self.grid.addWidget(TransactionWidget(self))

    def configure_menu_bar(self) -> None:
        """
        Setup the menu bar
        """
        exitAction = QAction(QIcon("exit.png"), "&Exit", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.setStatusTip("Exit application")
        exitAction.triggered.connect(app.quit)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu("&File")
        fileMenu.addAction(exitAction)

        walletActionCreate = QAction("&Create", self)
        walletActionCreate.setStatusTip("Create new wallet")
        walletActionCreate.triggered.connect(lambda: self.__add_wallet_widget("create"))

        walletActionLogin = QAction("&Login", self)
        walletActionLogin.setStatusTip("Login to wallet")
        walletActionLogin.triggered.connect(lambda: self.__add_wallet_widget("login"))

        walletActionLogout = QAction("&Logout", self)
        walletActionLogout.setStatusTip("Logout of wallet")
        walletActionLogout.triggered.connect(lambda: self.__add_wallet_widget("logout"))

        walletMenu = menubar.addMenu("&Wallet")
        walletMenu.addAction(walletActionCreate)
        walletMenu.addAction(walletActionLogin)
        walletMenu.addAction(walletActionLogout)

        chainActionRegister = QAction("&Register", self)
        chainActionRegister.setStatusTip("Register node to blockchain")
        chainActionRegister.triggered.connect(self.registerNode)

        chainActionSync = QAction("&Sync", self)
        chainActionSync.setStatusTip("Sync node to blockchain")
        chainActionSync.triggered.connect(self.syncNode)

        chainActionShow = QAction("&Show chain", self)
        chainActionShow.setStatusTip("Show blockchain")
        chainActionShow.triggered.connect(
            lambda: self.mainDisplay.setText(
                json.dumps(self.blockchain.pretty_chain(), indent=2)
            )
        )

        chainActionClear = QAction("&Clear", self)
        chainActionClear.setStatusTip("Clear visible blockchain")
        chainActionClear.triggered.connect(lambda: self.mainDisplay.setText(""))

        chainMenu = menubar.addMenu("&Chain")
        chainMenu.addAction(chainActionRegister)
        chainMenu.addAction(chainActionSync)
        chainMenu.addAction(chainActionShow)
        chainMenu.addAction(chainActionClear)

        transactionNew = QAction("&New", self)
        transactionNew.setStatusTip("Create new transaction")
        transactionNew.triggered.connect(self.__add_transaction_widget)

        transactionPending = QAction("&Pending", self)
        transactionPending.setStatusTip("View pending transaction(s)")
        transactionPending.triggered.connect(
            lambda: self.mainDisplay.setText(
                json.dumps(
                    [
                        t.to_ordered_dict()
                        for t in self.blockchain.get_open_transactions
                    ],
                    indent=2,
                )
            )
        )

        transactionMenu = menubar.addMenu("&Transaction")
        transactionMenu.addAction(transactionNew)
        transactionMenu.addAction(transactionPending)

        mineNewBlock = QAction("&Mine", self)
        mineNewBlock.setStatusTip("Mine a new block")
        mineNewBlock.triggered.connect(self.mineBlock)

        mineMenu = menubar.addMenu("&Mining")
        mineMenu.addAction(mineNewBlock)

    def setupUi(self):
        self.scroll = QScrollArea()
        self.widget = QWidget()

        # Set the layout
        self.grid = QGridLayout()

        # Initialize Status Bar
        self.statusBar()

        # Create and add top label
        self.label = QLabel("Welcome!!")
        self.label.setAlignment(Qt.AlignTop)
        self.grid.addWidget(self.label, 1, 0)

        # Create and connect main display
        self.mainDisplay = QLabel("")
        self.mainDisplay.setAlignment(Qt.AlignVCenter)
        self.grid.addWidget(self.mainDisplay, 2, 0)

        self.configure_menu_bar()

        self.widget.setLayout(self.grid)

        # Scroll Area Properties (Since our wallet addresses are so long right now)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)

        self.setCentralWidget(self.scroll)

        self.setWindowTitle("To Be Named Coin")
        self.setGeometry(1300, 1000, 1300, 1000)

    def registerNode(self):
        # 2. Instantiate the subclass of QRunnable
        runnable = Register(self.blockchain, self.statusBar)
        # 3. Call start()
        self.pool.start(runnable)

    def syncNode(self):
        # 2. Instantiate the subclass of QRunnable
        runnable = Sync(self.blockchain, self.wallet, self.label, self.statusBar)
        # 3. Call start()
        self.pool.start(runnable)

    def mineBlock(self):
        # 2. Instantiate the subclass of QRunnable
        runnable = MineBlock(self.blockchain, self.wallet, self.statusBar, self.label)
        # 3. Call start()
        self.pool.start(runnable)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
