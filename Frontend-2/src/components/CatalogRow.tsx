import "@/App.css";
import Flicking, {
  ViewportSlot,
} from "@egjs/react-flicking";
import "@egjs/react-flicking/dist/flicking.css";
import { Arrow } from "@egjs/flicking-plugins";
import "@egjs/flicking-plugins/dist/arrow.css";
import { useState, useRef, useEffect } from "react";
import RowImage from "./RowImage";
import Select from 'react-select'

const brandColors = { "rgb(138, 44, 32)": 0, "rgb(64, 127, 134)": 0, "rgb(215, 174, 82)": 0, "rgb(55, 118, 187)": 0 }

export default function CatalogRow(props: any) {
  const boom = useRef(null);
  const selectref = useRef(null);
  const _plugins = [new Arrow({ moveCount: 6 })];
  const [methods, setMethods] = useState([])
  const [lastmethods, setLast] = useState([])
  const [options, setOptions] = useState([])
  const [colorIndex, setColorIndex] = useState(() => {
    if (props.data.feature == "Brand Color") {
      return { "rgb(138, 44, 32)": 1, "rgb(64, 127, 134)": 0, "rgb(215, 174, 82)": 0, "rgb(55, 118, 187)": 0 }
    } else {
      return brandColors
    }
  })


  const handleClick = (e) => {

    props.onClick(e);
    setColorIndex(brandColors)
  };
  const handleColor = (e) => {

    setColorIndex(() => {

      let colorVals = { "rgb(138, 44, 32)": 0, "rgb(64, 127, 134)": 0, "rgb(215, 174, 82)": 0, "rgb(55, 118, 187)": 0 }
      colorVals[e.target.style.backgroundColor] = 1
      return colorVals
    })
    props.handleColor(e, props.index, methods, props.id)

  }
  const onInputChange = (data) => {

    setMethods(data.map((k) => k.label))
  };

  useEffect(() => {

    boom.current.moveTo(0);
    boom.current.resize();

  }, [props.resize]);
  useEffect(() => {
    setMethods(() => {
      if (Object.hasOwn(props.data, "tags")) {
        return props.data.tags.slice(0, 2)
      }
      return []
    })
    setLast(() => {
      if (Object.hasOwn(props.data, "tags")) {
        return props.data.tags.slice(0, 2)
      }
      return []
    })
    setOptions(() => {
      if (Object.hasOwn(props.data, "tags")) {
        return props.data.tags.map((k) => ({ value: k, label: k })).slice(0, 5)
      }
      return []
    })
    setColorIndex(() => {
      if (props.data.feature == "Brand Color") {
        return { "rgb(138, 44, 32)": 1, "rgb(64, 127, 134)": 0, "rgb(215, 174, 82)": 0, "rgb(55, 118, 187)": 0 }
      } else {
        return brandColors
      }
    })

  }
    , [props.changetags, props.clearstate]
  )

  const bom = () => {
    const s1 = [...lastmethods].sort()
    const s2 = [...methods].sort()

    if (JSON.stringify(s1) != JSON.stringify(s2)) {
      setColorIndex(brandColors)
      props.onmenu(methods, props.index)
    }
    setLast(methods)
  }

  const colors = <div className="flex items-center">
    <div className="badge badge-secondary cursor-pointer" style={colorIndex["rgb(138, 44, 32)"] == 1 ? { backgroundColor: "rgb(138, 44, 32)", borderColor: "white", borderWidth: "1px" } : { backgroundColor: "rgb(138,44,32)", border: "none" }} onClick={handleColor}></div>
    <div className="badge badge-secondary cursor-pointer" style={colorIndex["rgb(64, 127, 134)"] == 1 ? { backgroundColor: "rgb(64, 127, 134)", borderColor: "white", borderWidth: "1px" } : { backgroundColor: "rgb(64,127,134)", border: "none" }} onClick={handleColor}></div>
    <div className="badge badge-secondary cursor-pointer" style={colorIndex["rgb(215, 174, 82)"] == 1 ? { backgroundColor: "rgb(215, 174, 82)", borderColor: "white", borderWidth: "1px" } : { backgroundColor: "rgb(215,174,82)", border: "none" }} onClick={handleColor}></div>
    <div className="badge badge-secondary cursor-pointer" style={colorIndex["rgb(55, 118, 187)"] == 1 ? { backgroundColor: "rgb(55, 118, 187)", borderColor: "white", borderWidth: "1px" } : { backgroundColor: "rgb(55,118,187)", border: "none" }} onClick={handleColor}></div>
  </div>
  return (
    <div className="catalog-row">

      <div className=" category-div items-center gap-3 flex flex-row"><h1 className="category">{props.data.feature}</h1>
        {props.data.feature == 'Brand Color' &&
          colors
        }
        {props.data.type == "tagging_choice" && <div className="flex justify-center gap-3 items-center">

          <Select options={options} value={methods.map(k => ({ value: k, label: k }))} placeholder="Change Tags" controlShouldRenderValue={false} hideSelectedOptions={false} isMulti className="basic-multi-select"
            menuPortalTarget={document.body} ref={selectref}
            styles={{ menuPortal: base => ({ ...base, zIndex: 5 }) }}
            closeMenuOnSelect={false} isSearchable={false} onMenuClose={bom} onChange={onInputChange} />
          <div>{colors}
          </div></div>}
        {props.data.type == "tagging" &&
          colors}
        {props.data.type == "color" && <div className="badge badge-primary" style={{ backgroundColor: props.data.color, border: "none" }}></div>}
      </div>
      <div className="cursor-none" onMouseMove={props.onMouseMove} onMouseEnter={props.onMouseEnter} onMouseLeave={props.onMouseLeave}>
        <Flicking
          bound={true}

          renderOnSameKey={true}
          moveType="freeScroll"
          circular={false}
          cameraClass="flicking-bomb"
          ref={boom}
          align="prev"
          plugins={_plugins}
          useFindDOMNode={true}
        >
          {props.data.images.map((data: any, key: any) => (
            <RowImage
              key={key}
              src={data.src}
              width={data.width}
              height={data.height}
              draggable={false}
              onClick={handleClick}
            />
          ))}
          <ViewportSlot>
            <span className="flicking-arrow-prev" onMouseEnter={props.onMouseLeave} onMouseLeave={props.onMouseEnter}></span>
            <span className="flicking-arrow-next" onMouseEnter={props.onMouseLeave} onMouseLeave={props.onMouseEnter}></span>
          </ViewportSlot>
        </Flicking>
      </div>
    </div>


  );
}

