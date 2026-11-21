const ROOT_CLASS = "print-root";
const BODY_CLASS = "printing-target";

export function printElement(element: HTMLElement): void {
  const printRoot = document.createElement("div");
  printRoot.className = ROOT_CLASS;
  printRoot.append(element.cloneNode(true));
  const cleanup = () => {
    printRoot.remove();
    document.body.classList.remove(BODY_CLASS);
    window.removeEventListener("afterprint", cleanup);
  };
  document.body.append(printRoot);
  document.body.classList.add(BODY_CLASS);
  window.addEventListener("afterprint", cleanup);
  window.print();
}
