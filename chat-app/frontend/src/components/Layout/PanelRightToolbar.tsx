import React, { ReactNode } from "react";
import { Body1Strong, Button } from "@fluentui/react-components";
import eventBus from "./eventbus";
import { DismissRegular } from "@fluentui/react-icons";

interface PanelRightToolbarProps {
    panelTitle?: string | null;
    panelIcon?: ReactNode;
    children?: ReactNode;
    showDismiss?: boolean;
}

const PanelRightToolbar: React.FC<PanelRightToolbarProps> = ({
    panelTitle,
    panelIcon,
    children,
    showDismiss = false,
}) => {
    const handleDismiss = () => {
        eventBus.emit("setActivePanel", null);
    };

    const hasTitle = Boolean(panelTitle || panelIcon);

    return (
        <div
            className="panelToolbar"
            style={{
                display: "flex",
                alignItems: "center",
                justifyContent: hasTitle ? "space-between" : "flex-end",
                padding: "8px 12px",
                boxSizing: "border-box",
                minHeight: "40px",
                gap: "8px",
            }}
        >
            {hasTitle ? (
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
                    {panelTitle ? (
                        <Body1Strong
                            style={{
                                whiteSpace: "nowrap",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                            }}
                        >
                            {panelTitle}
                        </Body1Strong>
                    ) : null}
                </div>
            ) : null}
            <div
                className="panelTools"
                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0px",
                }}
            >
                {children}
                {showDismiss ? (
                    <Button
                        appearance="subtle"
                        icon={<DismissRegular />}
                        onClick={handleDismiss}
                        aria-label="Close panel"
                    />
                ) : null}
            </div>
        </div>
    );
};

export default PanelRightToolbar;
