from concurrent.futures import ProcessPoolExecutor, wait

class Tool:
    threads = 1

    def __init__(self, input_dir=None):
        self.input_dir = input_dir

    def setup(self):
        pass

    def loop(self, input_file):
        pass

    def teardown(self):
        pass

    def files(self):
        Utils.file_list_from_dir(self.input_dir, '*.tif')

    def run(self):
        self.setup()

        if self.threads > 1:
            self._run_parallel()
        else:
            self._run_linear()

        self.teardown()
    
    def _run_parallel(self):
        files = self.files()

        with ProcessPoolExecutor(self.threads) as exc:
            futures = [exc.submit(self.loop, input_file) for input_file in files]
            wait(futures)

    def _run_linear(self):
        files = self.files()
        for input_file in files:
            self.loop(input_file)


