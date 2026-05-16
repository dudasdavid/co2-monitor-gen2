import sys
LOG_FILE = "/startup_error.log"

def log_exception(exc):
    try:
        with open(LOG_FILE, "a") as f:
            f.write("\n\n=== MAIN ERROR ===\n")
            sys.print_exception(exc, f)
            f.write("\n")
    except:
        pass

try:
    import uasyncio as asyncio
    import shared_variables as var

    if var.hw_variant not in ["i80", "spi"]:
        raise OSError("Hardware variant is not selected!")
    if not var.debug:
        import main_dev
        asyncio.run(main_dev.main())
except Exception as e:
    # Print error so you can see it in the Thonny shell
    print("FATAL ERROR in main:", e)
    sys.print_exception(e)
    log_exception(e)