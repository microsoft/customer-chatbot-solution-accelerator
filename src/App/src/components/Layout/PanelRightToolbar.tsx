import { Body1Strong, Button } from "@fluentui/react-components";
import { DismissRegular } from "@fluentui/react-icons";
import React, { ReactNode } from "react";
import eventBus from "./eventbus";

interface PanelRightToolbarProps {
    panelTitle?: string | null;
    panelIcon?: ReactNode;
    children?: ReactNode;
    handleDismiss?: () => void;
}

const PanelRightToolbar: React.FC<PanelRightToolbarProps> = ({
    panelTitle,
    panelIcon,
    children,
}) => {
    const handleDismiss = () => {
        eventBus.emit("setActivePanel", null); // Close the current panel
    };

    return (
        <div
            className="panelToolbar"
            style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "16px",
                boxSizing: "border-box",
                height: "56px",
                gap: "8px",
            }}
        >
            <div
                className="panelTitle"
                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    flex: "1 1 auto",
                    overflow: "hidden",
                }}
            >
                {panelIcon && (
                    <div
                        style={{
                            flexShrink: 0,
                            display: "flex",
                            alignItems: "center",
                        }}
                    >
                        {panelIcon}
                    </div>
                )}
                {panelTitle && (
                    <Body1Strong
                        style={{
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                        }}
                    >
                        {panelTitle}
                    </Body1Strong>
                )}
            </div>
            <div
                className="panelTools"
                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0px",
                }}
            >
                {children}
                <Button
                    appearance="subtle"
                    icon={<DismissRegular />}
                    onClick={handleDismiss}
                    aria-label="Close panel"
                    title="Close"
                />
            </div>
        </div>
    );
};

export default PanelRightToolbar;
