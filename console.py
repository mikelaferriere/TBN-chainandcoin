import logging
import sys
import json
import traceback

from uuid import uuid4

from PyQt5.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSlot, pyqtSignal
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
from util.logging0 import configure_logging
from walletv2 import Wallet

configure_logging()


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    - finished: No data
    - error:`tuple` (exctype, value, traceback.format_exc() )
    - result: `object` data returned from processing, anything
    - progress: `tuple` indicating progress metadata
    """

    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(tuple)


class Worker(QRunnable):
    """
    Worker thread
    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
    """

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs["progress_callback"] = self.signals.progress

    @pyqtSlot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


class Window(
    QMainWindow
):  # pylint: disable=too-many-instance-attributes,too-many-locals,too-many-statements
    def __init__(self):
        super().__init__()
        self.node_id = str(uuid4())
        self.wallet = Wallet()
        self.blockchain = Blockchain(self.wallet.address, self.node_id)
        self.threadCount = QThreadPool.globalInstance().maxThreadCount()
        self.pool = QThreadPool.globalInstance()

        self.setWindowTitle("To Be Named Coin")
        self.setGeometry(1300, 1000, 1300, 1000)

        self.setupUi()
        self.registerAndSyncNode()

    def format_label(self) -> None:
        balance = (
            0.0
            if self.blockchain.get_balance() is None
            else self.blockchain.get_balance()
        )
        self.label.setText(
            "Address: {}\nBalance: {:6.2f}".format(self.wallet.address, balance)
        )

    def configure_menu_bar(self) -> None:
        """
        Setup the menu bar
        """
        exitAction = QAction(QIcon("exit.png"), "&Exit", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.setStatusTip("Exit application")
        exitAction.triggered.connect(app.quit)  # type: ignore

        menubar = self.menuBar()
        fileMenu = menubar.addMenu("&File")
        fileMenu.addAction(exitAction)

        walletActionCreate = QAction("&Create", self)
        walletActionCreate.setStatusTip("Create new wallet")
        walletActionCreate.triggered.connect(  # type: ignore
            lambda: self.setupWalletUi("create")
        )

        walletActionLogin = QAction("&Login", self)
        walletActionLogin.setStatusTip("Login to wallet")
        walletActionLogin.triggered.connect(  # type: ignore
            lambda: self.setupWalletUi("login")
        )

        walletActionLogout = QAction("&Logout", self)
        walletActionLogout.setStatusTip("Logout of wallet")
        walletActionLogout.triggered.connect(  # type: ignore
            lambda: self.setupWalletUi("logout")
        )

        walletMenu = menubar.addMenu("&Wallet")
        walletMenu.addAction(walletActionCreate)
        walletMenu.addAction(walletActionLogin)
        walletMenu.addAction(walletActionLogout)

        chainActionRegister = QAction("&Register and sync", self)
        chainActionRegister.setStatusTip("Register and sync node to blockchain")
        chainActionRegister.triggered.connect(self.registerAndSyncNode)  # type: ignore

        chainActionShow = QAction("&Show chain", self)
        chainActionShow.setStatusTip("Show blockchain")
        chainActionShow.triggered.connect(  # type: ignore
            lambda: self.mainDisplay.setText(
                json.dumps(self.blockchain.pretty_chain(), indent=2)
            )
        )

        chainActionClear = QAction("&Clear", self)
        chainActionClear.setStatusTip("Clear visible blockchain")
        chainActionClear.triggered.connect(  # type: ignore
            lambda: self.mainDisplay.setText("")
        )

        chainMenu = menubar.addMenu("&Chain")
        chainMenu.addAction(chainActionRegister)
        chainMenu.addAction(chainActionShow)
        chainMenu.addAction(chainActionClear)

        transactionNew = QAction("&New", self)
        transactionNew.setStatusTip("Create new transaction")
        transactionNew.triggered.connect(self.setupTransactionUi)  # type: ignore

        transactionPending = QAction("&Pending", self)
        transactionPending.setStatusTip("View pending transaction(s)")
        transactionPending.triggered.connect(  # type: ignore
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
        mineNewBlock.triggered.connect(self.mineBlock)  # type: ignore

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

        self.widget.setLayout(self.grid)
        self.widget.setFixedWidth(self.width())

        # Scroll Area Properties (Since our wallet addresses are so long right now)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.widget)

        self.setCentralWidget(self.scroll)
        self.configure_menu_bar()

    def setupWalletUi(self, action) -> None:
        self.mainDisplay.setText("")

        walletLayout = QGridLayout()
        password = QInputDialog()

        def refresh_chain() -> None:
            self.blockchain = Blockchain(self.wallet.address, self.node_id)
            self.registerAndSyncNode()
            self.format_label()

        def login() -> None:
            if self.wallet.login(password.textValue()):
                refresh_chain()

        def create() -> None:
            if self.wallet.create_login(password.textValue()):
                refresh_chain()

        if action == "logout":
            self.wallet = Wallet()
            refresh_chain()
        else:
            password.setTextEchoMode(QLineEdit.Password)
            if action == "create":
                password.accepted.connect(create)  # type: ignore
            elif action == "login":
                password.accepted.connect(login)  # type: ignore

            walletLayout.addWidget(password, 1, 0)
            self.grid.addLayout(walletLayout, 2, 0)

    def setupTransactionUi(self) -> None:
        self.mainDisplay.setText("")

        transactionLayout = QGridLayout()
        recipientLabel = QLabel("Recipient: ")
        recipient = QLineEdit()
        amountLabel = QLabel("Amount: ")
        amount = QLineEdit()
        submit = QPushButton("Submit Transaction")

        def submit_transaction():
            signature = self.wallet.sign_transaction(
                self.wallet.address, recipient.text(), amount.text()
            )
            transaction = Transaction(
                sender=self.wallet.address,
                recipient=recipient.text(),
                amount=amount.text(),
                signature=signature,
            )

            if self.blockchain.add_transaction(transaction):
                logging.info("Added transaction!")
                # Theres got to be a better way to handle these Widgets...
                recipient.deleteLater()
                recipientLabel.deleteLater()
                amount.deleteLater()
                amountLabel.deleteLater()
                submit.deleteLater()
            else:
                logging.info("Transaction failed!")

        submit.clicked.connect(submit_transaction)  # type: ignore

        transactionLayout.addWidget(recipientLabel, 1, 0)
        transactionLayout.addWidget(recipient, 1, 1)
        transactionLayout.addWidget(amountLabel, 2, 0)
        transactionLayout.addWidget(amount, 2, 1)
        transactionLayout.addWidget(submit, 3, 0)
        self.grid.addLayout(transactionLayout, 3, 0)

    def registerAndSyncNode(self):
        def log_result(s):
            self.statusBar().showMessage(s)

        def finished():
            self.format_label()

        def progress(progress):
            progress, message = progress
            logging.debug("%d%% done %s", progress, message)

        def register(progress_callback):
            logging.info("Registering to masternode....")
            progress_callback.emit((25, "Registering to masternode"))
            self.blockchain.register_node("https://sedrik.life/blockchain")
            progress_callback.emit((50, "Registered to masternode"))
            logging.info("Syncing with masternode....")
            progress_callback.emit((75, "Syncing to masternode..."))
            self.blockchain.resolve_conflicts()
            progress_callback.emit(
                (100, f"Synced {self.blockchain.chain_length} blocks with masternode")
            )

        # Pass the function to execute
        worker = Worker(
            register
        )  # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(log_result)
        worker.signals.finished.connect(finished)
        worker.signals.progress.connect(progress)
        # Execute
        self.pool.start(worker)

    def mineBlock(self):
        def log_result(s):
            self.statusBar().showMessage(s)

        def finished():
            self.format_label()
            logging.info("Finished")

        def progress(progress):
            progress, message = progress
            logging.debug("%d%% done %s", progress, message)

        def register(progress_callback):
            logging.info("Mining new Block...")
            progress_callback.emit((50, "Mining new block..."))
            self.blockchain.mine_block()
            progress_callback.emit((100, "Block Mined!"))

        # Pass the function to execute
        worker = Worker(
            register
        )  # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(log_result)
        worker.signals.finished.connect(finished)
        worker.signals.progress.connect(progress)
        # Execute
        self.pool.start(worker)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
