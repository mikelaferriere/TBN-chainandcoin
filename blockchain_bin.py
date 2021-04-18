import json
import click

from blockchain import Blockchain
from transaction import Transaction


@click.group()
def cli():
    pass


@cli.command("run")
def run() -> None:
    chain = Blockchain()
    chain.new_transaction(
        Transaction(sender="HenryCoinAddress", recipient="SteveCoinAddress", amount=10)
    )
    chain.mine("BillCoinAddress")
    chain.new_transaction(
        Transaction(sender="HenryCoinAddress", recipient="SteveCoinAddress", amount=7)
    )
    chain.new_transaction(
        Transaction(sender="HenryCoinAddress", recipient="SteveCoinAddress", amount=5)
    )
    chain.mine("BillCoinAddress")

    print(json.dumps(chain.pretty_chain(), indent=2, default=str))


if __name__ == "__main__":
    cli(obj={})  # pylint: disable=unexpected-keyword-arg, no-value-for-parameter
