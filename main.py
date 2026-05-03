import liveJarvis
import eyes
import brain_service_one
import brain_service_two
import actions
import ai_client


mode = False

def main():
    # Initializes and caches models
    ai_client.initialize()
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