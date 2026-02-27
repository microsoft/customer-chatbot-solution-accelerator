import React, { useState, useEffect, ReactNode, ReactElement } from "react";
import eventBus from "./eventbus";
import PanelRightToolbar from "./PanelRightToolbar";

interface PanelRightProps {
  panelWidth?: number; // Optional width of the panel
  panelResize?: boolean; // Whether resizing is enabled
  panelType: "first" | "second" | "third" | "fourth"; // Panel type identifier
  defaultClosed?: boolean;
  children?: ReactNode;
}

const PanelRight: React.FC<PanelRightProps> = ({
  panelWidth = 325, // Default width if not provided
  panelResize = true,
  panelType = "first", // Default to "first" if not explicitly defined
  defaultClosed = false,
  children,
}) => {
  const [isActive, setIsActive] = useState(() =>
    defaultClosed ? false : panelType === "first"
  );
  const [width, setWidth] = useState<number>(panelWidth); // Initial width from props or default
  const [isHandleHovered, setIsHandleHovered] = useState(false);

  useEffect(() => {
    if (eventBus.getPanelWidth() === 400) {
      eventBus.setPanelWidth(panelWidth); // Use the provided panelWidth prop
    }
    setWidth(eventBus.getPanelWidth()); // Set the current width from EventBus

    const handleActivePanel = (panel: "first" | "second" | "third" | "fourth" | null) => {
      setIsActive(panel === panelType); // Check if this panelType matches the active panel
    };

    const handleWidthChange = (newWidth: number) => {
      setWidth(newWidth); // Update width when EventBus notifies
    };

    eventBus.on("setActivePanel", handleActivePanel);
    eventBus.on("panelWidthChanged", handleWidthChange);

    return () => {
      eventBus.off("setActivePanel", handleActivePanel);
      eventBus.off("panelWidthChanged", handleWidthChange);
    };
  }, [panelType, panelWidth]);

  useEffect(() => {
    eventBus.emit("panelInitState", {
      panelType,
      isActive,
    });
  }, []);

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!panelResize) return;

    const startX = e.clientX;
    const startWidth = width;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const newWidth = Math.min(
        500, // Max width
        Math.max(256, startWidth - (moveEvent.clientX - startX)) // Min width
      );
      setWidth(newWidth);
      eventBus.setPanelWidth(newWidth); // Persist the new width in EventBus
    };

    const onMouseUp = () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      document.body.style.userSelect = "";
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);

    document.body.style.userSelect = "none";
  };

  if (!isActive) return null; // Do not render if not active

  const childrenArray = React.Children.toArray(children) as ReactElement[];
  const toolbar = childrenArray.find(
    (child) => React.isValidElement(child) && child.type === PanelRightToolbar
  );
  const content = childrenArray.filter(
    (child) => !(React.isValidElement(child) && child.type === PanelRightToolbar)
  );

  return (
    <div
      className={`panelRight ${panelResize ? 'panel-divider' : ''}`}
      style={{
        width: `${width}px`,
        display: "flex",
        flexDirection: "column",
        backgroundColor: "var(--coral-bg-primary)",
        height: "100%",
        boxSizing: "border-box",
        position: "relative",
        borderLeft: panelResize
          ? isHandleHovered
            ? "2px solid var(--colorNeutralStroke2)"
            : "1px solid"
          : "none",
      }}
    >
      {toolbar && <div style={{ flexShrink: 0 }}>{toolbar}</div>}

      <div
        className="panelContent"
        style={{
          flex: 1,
          overflowY: "auto",
        }}
      >
        {content}
      </div>

      {panelResize && (
        <div
          className="resizeHandle panel-divider"
          onMouseDown={handleMouseDown}
          onMouseEnter={() => setIsHandleHovered(true)}
          onMouseLeave={() => setIsHandleHovered(false)}
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "2px",
            height: "100%",
            cursor: "ew-resize",
            zIndex: 1,
            backgroundColor: isHandleHovered
              ? "var(--colorNeutralStroke2)"
              : "transparent",
          }}
        />
      )}
    </div>
  );
};

export default PanelRight;
