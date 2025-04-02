import React, { createContext, useState } from "react";

import { useFeedbackBox } from "@nypl/design-system-react-components";
import { ChakraComponent } from "@chakra-ui/react";

type FeedbackContextType = {
  onOpen: () => void;
  FeedbackBox: ChakraComponent<any>;
  onClose: () => void;
  isOpen?: boolean;
  isError: boolean | null;
  setIsError: React.Dispatch<React.SetStateAction<boolean | null>>;
  notificationText: string | null;
  setNotificationText: React.Dispatch<React.SetStateAction<string | null>>;
  statusCode: number | null;
  setStatusCode: React.Dispatch<React.SetStateAction<number | null>>;
};

export const FeedbackContext = createContext<FeedbackContextType | undefined>(
  undefined
);

export const FeedbackProvider: React.FC<{
  children?: React.ReactNode;
}> = ({ children }) => {
  const { FeedbackBox, isOpen, onOpen, onClose } = useFeedbackBox();
  const [isError, setIsError] = useState(null);
  const [notificationText, setNotificationText] = useState(null);
  const [statusCode, setStatusCode] = useState(null);

  return (
    <FeedbackContext.Provider
      value={{
        onOpen,
        FeedbackBox,
        isOpen,
        onClose,
        isError,
        setIsError,
        notificationText,
        setNotificationText,
        statusCode,
        setStatusCode,
      }}
    >
      {children}
    </FeedbackContext.Provider>
  );
};
