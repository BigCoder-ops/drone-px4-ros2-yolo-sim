import pygame

def init():
    """Initializes the pygame window to capture key presses."""
    pygame.init()
    win = pygame.display.set_mode((400, 400))

def getKey(keyName):
    """
    Checks if a specific key is pressed.
    Example usage: getKey('LEFT') or getKey('a')
    """
    ans = False
    for eve in pygame.event.get(): pass
    keyInput = pygame.key.get_pressed()
    myKey = getattr(pygame, 'K_{}'.format(keyName))
    
    if keyInput[myKey]:
        ans = True
        
    pygame.display.update()
    return ans

if __name__ == '__main__':
    init()
    while True:
        if getKey('LEFT'):
            print('Left key pressed')
        if getKey('RIGHT'):
            print('Right key pressed')
