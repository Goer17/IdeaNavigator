import os
from dotenv import find_dotenv, load_dotenv
from argparse import ArgumentParser
from mcts.node import (
    Node,
    Context,
    root_node
)
from mcts.runner import (
    MCTSRunner
)
from agents.generator import (
    TestGenerator,
    SciGenerator
)
from agents.feedbacker import (
    SimpleFeedbacker
)
from agents.rewarder import (
    TestRewarder
)
from rag.general import (
    TestRAG
)

load_dotenv(find_dotenv())

api_key = os.environ["API_KEY"]
base_url = os.environ["BASE_URL"]

def mcts_demo():
    generator = TestGenerator()
    rewarder = TestRewarder()
    runner = MCTSRunner(
        root=Node(
            context=root_node()
        ),
        generator=generator,
        rewarder=rewarder,
        sampling_method="epsilon",
        epsilon=0.1,
        exploration_wright=2.0
    )
    runner.run(
        n_rollouts=50,
        n_exp=3,
        terminal_func=lambda contexts: sum(int(context.content) for context in contexts) >= len(rewarder.path)
    )

def sci_generator():
    task = "Generated some scientific research idea related to language model compression"
    generator = SciGenerator(
        api_key=api_key,
        base_url=base_url,
        task=task,
        model='gpt-4o'
    )
    feedbacker = SimpleFeedbacker(
        base_url=base_url,
        api_key=api_key
    )
    contexts = []
    while True:
        gen_context = generator.generate(
            contexts=contexts
        )
        print(gen_context)
        contexts.append(gen_context)
        if gen_context.key == "search":
            gen_context.observation = feedbacker.feedback(contexts=contexts)
            print(f"[result]\n{gen_context.observation}")
        if gen_context.key == "gen_idea":
            break


def main():
    parser = ArgumentParser()
    parser.add_argument("-f", "--func", required=True, help="The testing function")

    args = parser.parse_args()
    func = args.func
    eval(func)()

if __name__ == "__main__":
    main()