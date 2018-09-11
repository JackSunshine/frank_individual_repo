from rest.client.manager import RestClient


if __name__ == '__main__':
    client = RestClient.get_client('100.7.33.187')
    client.get_vm_network()
