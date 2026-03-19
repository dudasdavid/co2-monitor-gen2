import uasyncio as asyncio
import sys
import main_dev

try:
    asyncio.run(main_dev.main())
except Exception as e:
    # Print error so you can see it in the Thonny shell
    print("FATAL ERROR in main:", e)
    sys.print_exception(e)