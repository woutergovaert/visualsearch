import "@/App.css";
import React, { useState, useRef, useEffect } from "react";

export default function RowImage(props: any) {
    const [animation, setAnimation] = useState(false)

    const handleClick = (e) => {
        setAnimation(true)
        props.onClick(e);
    }
    return (
        <img ref={props.elRef}
            src={props.src}
            onAnimationEnd={() => setAnimation(false)}
            className={animation ? 'animated catalog-card' : "catalog-card"}
            style={{
                width: (props.width / props.height) * 250,
                height: "250px",
            }}

            draggable={false}
            onClick={handleClick}
        />
    )
}
