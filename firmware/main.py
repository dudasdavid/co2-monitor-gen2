import uasyncio as asyncio
import sys

import shared_variables as var

try:
    if var.hw_variant not in ["i80", "spi"]:
        raise OSError("Hardware variant is not selected!")
    import main_dev
    asyncio.run(main_dev.main())
except Exception as e:
    # Print error so you can see it in the Thonny shell
    print("FATAL ERROR in main:", e)
    sys.print_exception(e)