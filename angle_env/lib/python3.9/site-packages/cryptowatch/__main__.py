import sys
import cryptowatch


# Provide basic utility when the module
# is run as a script via the -m option.
def main():

    try:
        market = sys.argv[1]
    except:
        market = "kraken:btcusd"
    else:
        if ":" not in market:
            market = "kraken:{}".format(market)

    try:
        print(cryptowatch.markets.get(market).market.price.last)
    except:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":

    main()
