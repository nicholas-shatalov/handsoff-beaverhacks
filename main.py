import brain_service_one
import brain_service_two
from nemotron_voice_jarvis import liveJarvis
import eyes
import actions

mode = False
def main():
    while True:
        if mode:
            eyes.main()
        else:
            liveJarvis.main()
        brain_service_one.start_brain_service()
        brain_service_two.start_brain_service()
        actions.execute_tasks()

if __name__ == "__main__":
    main()