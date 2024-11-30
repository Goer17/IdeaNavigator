from typing import (
    Dict, List, Literal,
    Callable
)
from .node import Context, Node
from agents.generator import (
    Generator
)
from agents.rewarder import (
    Rewarder
)

class MCTSRunner:
    def __init__(self,
                 root: Node,
                 generator: Generator,
                 rewarder: Rewarder,
                 sampling_method: Literal["best", "epsilon", "v-epsilon"] = "best",
                 *args, **kwargs
                 ):
        self.root = root
        self.generator = generator
        self.rewarder = rewarder
        self.sampling_method = sampling_method
        self.best_rollout = None
        self.pre_contexts = []
        if self.sampling_method in ["epsilon", "v-epsilon"]:
            self.epsilon = kwargs.get("epsilon", 0.2)
    
    def __expand(self,
                 current_node: Node,
                 contexts: List[Context],
                 n_exp: int
                 ) -> Context:
        for i in range(n_exp):
            child_context = self.generator.generate(
                contexts=contexts
            )
            child_node = Node(
                context=child_context,
                parent=current_node,
                depth=current_node.depth + 1
            )
            current_node.children.append(child_node)
    
    def __backprop(self,
                   leaf_node: Node,
                   reward: float
                   ):
        node = leaf_node
        while node:
            node.update(reward=reward)
            node = node.parent
    
    def __rollout(self,
                  contexts: List[Context],
                  terminal_func: Callable
                  ) -> List[Context]:
        rollout = contexts[:]
        while not terminal_func(rollout):
            gen_context = self.generator.generate(contexts=rollout)
            rollout.append(gen_context)
        return rollout
    
    def __run_one_trial(self,
            n_rollouts: int,
            n_exp: int,
            terminal_func: Callable
            ):
        cnt_rollouts = 0
        while cnt_rollouts < n_rollouts:
            current_node = self.root
            contexts = self.pre_contexts[:]
            while not current_node.is_leaf():
                if self.sampling_method == "best":
                    current_node = current_node.best_child() # select
                elif self.sampling_method == "epsilon":
                    current_node = current_node.epsilon_sample(epsilon=self.epsilon)
                elif self.sampling_method == "v-epsilon":
                    current_node = current_node.epsilon_sample(epsilon=self.epsilon / self.root.visits)
                if current_node != self.root:
                    contexts.append(current_node.context)
            if terminal_func(contexts):
                return
            if current_node.visits > 0 or current_node == self.root:
                self.__expand(current_node=current_node, contexts=contexts, n_exp=n_exp) # expand
                current_node = current_node.children[0]
            rollout = self.__rollout(contexts=contexts, terminal_func=terminal_func) # rollout
            reward = self.rewarder.get_reward(rollout)
            if self.best_rollout is None or self.best_rollout["reward"] < reward:
                self.best_rollout = {
                    "rollout": rollout,
                    "reward": reward
                }
            self.__backprop(leaf_node=current_node, reward=reward) # back propagation
            cnt_rollouts += 1
            print(f"rollout {cnt_rollouts} was over, current best value : {self.best_rollout['reward']}")
            
    
    def __next_step(self) -> bool:
        self.root = self.root.best_child()
        if self.root is None:
            return False
        self.pre_contexts.append(self.root.context)
        self.root.clear()
        return True
    
    def run(self,
            n_trials: int = -1,
            n_rollouts: int = 10,
            n_exp: int = 5,
            terminal_func: Callable = lambda contexts: contexts[-1].key == "terminate"
            ):
        cnt_trials = 0
        while n_trials < 0 or cnt_trials < n_trials:
            print(f"trial {cnt_trials}:")
            self.__run_one_trial(
                n_rollouts=n_rollouts,
                n_exp=n_exp,
                terminal_func=terminal_func
            )
            if not self.__next_step():
                # terminal node
                print(f"all trials were over, best value = {self.best_rollout['reward']}")
                break
            cnt_trials += 1
            print(f"next step:\n{self.root.context}")
        