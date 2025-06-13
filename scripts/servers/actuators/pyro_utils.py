from typing import Optional
import Pyro5.api

class Pyro5Mixin:
    """
    Mixin to make any class accessible via Pyro5.
    It registers the class instance with the given Pyro5 daemon upon initialization.
    """

    def __init__(
        self, *args, daemon: Pyro5.api.Daemon, object_id: Optional[str] = None, **kwargs
    ):
        # Call the original class's __init__
        super().__init__(*args, **kwargs)

        # store the daemon
        self.daemon = daemon

        # Register the object with the daemon
        self._pyro_uri = self.daemon.register(self, objectId=object_id)
        print(f"[Pyro5Mixin] Registered with URI: {self._pyro_uri}")

    def run(self):
        self.daemon.requestLoop()

    @property
    def pyro_uri(self):
        return self._pyro_uri



