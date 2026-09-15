"""A simple Tkinter GUI for the ExpertCook expert system.

Run it with:

    venv/Scripts/python.exe ui.py

Pick a dish, set the parameters (RICE FIRST - it is the base everything else
is derived from), and click "Generate Guide". The parameter widgets are built
automatically from ``expertcook.recipes.PARAM_SPECS`` (the same source the
CLI and web server use), so all interfaces always stay in sync.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from expertcook.recipes import DISHES, PARAM_SPECS
from expertcook.planner import build_plan


TITLE_FONT = ("Segoe UI", 16, "bold")
LABEL_FONT = ("Segoe UI", 10)
HELP_FONT = ("Segoe UI", 8, "italic")
OUTPUT_FONT = ("Consolas", 10)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ExpertCook - Rice Dishes Expert System")
        self.geometry("900x720")
        self.minsize(720, 600)

        self._dish_keys = list(DISHES)
        self._dish_names = [DISHES[k] for k in self._dish_keys]
        self._param_vars = {}          # param name -> tk.StringVar

        self._build_layout()
        self._render_params()          # initial params for the first dish

    # ------------------------------------------------------------------ UI
    def _build_layout(self):
        header = ttk.Frame(self, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(header, text="ExpertCook", font=TITLE_FONT).pack(anchor="w")
        ttk.Label(header,
                  text="Rice is the base ingredient - set the rice and every "
                       "other quantity follows from it.",
                  font=LABEL_FONT, foreground="#555").pack(anchor="w")

        controls = ttk.Frame(self, padding=(16, 4))
        controls.pack(fill="x")

        ttk.Label(controls, text="Dish:", font=LABEL_FONT).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        self._dish_var = tk.StringVar(value=self._dish_names[0])
        dish_box = ttk.Combobox(controls, textvariable=self._dish_var,
                                values=self._dish_names, state="readonly", width=24)
        dish_box.grid(row=0, column=1, sticky="w", pady=6)
        dish_box.bind("<<ComboboxSelected>>", lambda e: self._render_params())

        # Frame that is rebuilt whenever the dish changes.
        self._params_frame = ttk.LabelFrame(self, text="Parameters",
                                            padding=(16, 8))
        self._params_frame.pack(fill="x", padx=16, pady=(8, 4))

        actions = ttk.Frame(self, padding=(16, 4))
        actions.pack(fill="x")
        ttk.Button(actions, text="Generate Guide",
                   command=self._generate).pack(side="left")
        ttk.Button(actions, text="Clear",
                   command=lambda: self._set_output("")).pack(side="left", padx=8)

        out_frame = ttk.LabelFrame(self, text="Cooking guide", padding=(8, 8))
        out_frame.pack(fill="both", expand=True, padx=16, pady=(4, 16))
        self._output = scrolledtext.ScrolledText(
            out_frame, wrap="word", font=OUTPUT_FONT, state="disabled",
            background="#fbfbf8")
        self._output.pack(fill="both", expand=True)

    def _current_dish_key(self):
        return self._dish_keys[self._dish_names.index(self._dish_var.get())]

    def _render_params(self):
        for child in self._params_frame.winfo_children():
            child.destroy()
        self._param_vars = {}

        dish = self._current_dish_key()
        for row, spec in enumerate(PARAM_SPECS[dish]):
            ttk.Label(self._params_frame, text=spec["label"] + ":",
                      font=LABEL_FONT).grid(row=row, column=0, sticky="w",
                                            padx=(0, 10), pady=5)
            var = tk.StringVar(value=str(spec["default"]))
            self._param_vars[spec["name"]] = var

            if spec["type"] == "choice":
                widget = ttk.Combobox(self._params_frame, textvariable=var,
                                      values=spec["choices"], state="readonly",
                                      width=18)
            else:
                step = spec.get("step", 1)
                widget = ttk.Spinbox(self._params_frame,
                                     from_=spec.get("min", 1), to=1000,
                                     increment=step, textvariable=var, width=10)
            widget.grid(row=row, column=1, sticky="w", pady=5)

            if spec.get("help"):
                ttk.Label(self._params_frame, text=spec["help"], font=HELP_FONT,
                          foreground="#777").grid(row=row, column=2, sticky="w",
                                                  padx=(12, 0))
        self._set_output("")

    # --------------------------------------------------------------- action
    def _generate(self):
        dish = self._current_dish_key()
        params = {name: var.get() for name, var in self._param_vars.items()}
        try:
            plan = build_plan(dish, params)
        except ValueError as exc:
            messagebox.showerror("Invalid parameters", str(exc))
            return
        self._set_output(self._format_plan(plan))

    @staticmethod
    def _format_plan(plan):
        lines = []
        lines.append("COOKING GUIDE: %s" % plan["dish"])
        lines.append("=" * 58)
        for line in plan["summary"]:
            lines.append(line)
        lines.append("-" * 58)
        lines.append("INGREDIENTS (rice is the base):")
        for ing in plan["ingredients"]:
            amt = ing["amount"] if ing["amount"] is not None else "to taste"
            unit = ing["unit"]
            line = "  - %s: %s%s" % (ing["label"], amt,
                                     (" " + unit) if unit else "")
            if ing.get("note"):
                line += "   (%s)" % ing["note"]
            lines.append(line)
        lines.append("-" * 58)
        for i, step in enumerate(plan["steps"], 1):
            head = "Step %d" % i
            if step["phase"]:
                head += "  -  %s" % step["phase"]
            lines.append("")
            lines.append(head)
            for text_line in step["text"].splitlines():
                lines.append("  " + text_line)
        lines.append("")
        lines.append("=" * 58)
        lines.append("Enjoy your meal!")
        return "\n".join(lines)

    def _set_output(self, text):
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        if text:
            self._output.insert("1.0", text)
        self._output.configure(state="disabled")


def build_app():
    """Construct and return the App (without starting the event loop)."""
    return App()


def main():
    build_app().mainloop()


if __name__ == "__main__":
    main()
