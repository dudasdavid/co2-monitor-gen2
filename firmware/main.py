import uasyncio as asyncio
import sys

try:
    pass
    import main_dev
    asyncio.run(main_dev.main())
except Exception as e:
    # Print error so you can see it in the Thonny shell
    print("FATAL ERROR in main:", e)
    sys.print_exception(e)