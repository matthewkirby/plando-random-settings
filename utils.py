import os

def cleanup(file_to_delete):
    """ Delete residual files that are no longer needed """
    if os.path.isfile(file_to_delete):
        os.remove(file_to_delete)

def geometric_weights(N, startat=0, rtype="list"):
    """ Compute weights according to a geometric distribution """
    if rtype == "list":
        return [50.0/2**i for i in range(N)]
    elif rtype == "dict":
        return {str(startat+i): 50.0/2**i for i in range(N)}