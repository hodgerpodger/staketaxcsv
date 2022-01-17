import logging
import time


class Stage:
    def __init__(self, total_tasks, seconds_per_tasks):
        self.current_task_number = 0
        self.total_tasks = total_tasks
        self.seconds_per_task = seconds_per_tasks

    def update_task_number(self, task_number):
        self.current_task_number = task_number

    def seconds_remaining(self):
        return self.seconds_per_task * (self.total_tasks - self.current_task_number)


class Progress:
    def __init__(self, localconfig):
        self.time_start = time.time()
        self.stages = {}
        self.localconfig = localconfig

    def add_stage(self, stage_name, num_tasks, seconds_per_task):
        self.stages[stage_name] = Stage(num_tasks, seconds_per_task)

    def report_message(self, message):
        if self.localconfig.job:
            self.localconfig.job.set_message(message)
        logging.info({"message": message})

    def report(self, num, message, stage_name="default"):
        if stage_name in self.stages:
            stage = self.stages[stage_name]
            stage.update_task_number(num)
        else:
            logging.critical(f"Bad stage={stage_name} in {type(self).__name__}.report()")
            return

        seconds_left = sum(stage.seconds_remaining() for stage in self.stages.values())

        # Write to db
        if self.localconfig.job:
            estimated_completion_timestamp = int(time.time() + seconds_left)
            self.localconfig.job.set_in_progress(message, estimated_completion_timestamp)
        else:
            logging.info(
                "message: %s, seconds_left: %s, time_elapsed: %s", message, seconds_left, time.time() - self.time_start
            )
