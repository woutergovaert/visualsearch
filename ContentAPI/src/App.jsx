import { Suspense, useRef, useState } from 'react'
import './App.css'
import BasicExampleForm from './components/Myform';
import { FormThemeProvider } from 'react-form-component';
import Select from 'react-select'
import { Gallery } from "react-grid-gallery";

const options = [
  { value: 'ImageTagging', label: 'Tagging' },
  { value: 'OCR', label: 'OCR' },
  { value: 'ImageDescription', label: 'Image Description' },
  { value: 'Custom', label: 'Custom' }
]

function App() {
  const empty = { 'ImageTagging': [], 'ImageDescription': '', 'OCR': '', 'Custom': [], }
  const all = ['ImageTagging', 'OCR', 'ImageDescription', 'Custom']
  const [imgURL, setURL] = useState('')
  const [methods, setMethods] = useState(all)
  const [images, setImages] = useState([])
  const [data, setData] = useState(empty)
  const inputurl = useRef(null)
  const url = 'http://localhost:5020/call_api'
  const [loading, setLoad] = useState(false)

  const submitHandle = () => {
    setLoad(true)
    setURL(inputurl.current.value)
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        "url": inputurl.current.value, "methods": methods
      })

    })
      .then((res) => res.json())
      .then((res) => {

        setData(res)
        setLoad(false)

      })
  }

  const onInputChange = (
    data
  ) => {
    let methodss = data.map((k) => k.value)
    if (methodss.length === 0) {
      methodss = all

    }
    console.log(methodss)

    setMethods(methodss)

  };

  return (
    <div>
      <div className="navbar bg-base-100 justify-evenly mb-9">
        <div className="navbar-start">
          <a className="btn btn-ghost normal-case text-xl">API Test</a>
        </div>

        <div className="navbar-center hidden lg:flex gap-x-10 w-3/5 justify-center">
          <input type="text" placeholder="Image URL" className="input input-bordered input-secondary w-80" ref={inputurl} />
          <Select options={options} isMulti className="w-3/5 z-50 basic-multi-select " closeMenuOnSelect={false} isSearchable={false} onChange={onInputChange} />
          <button
            className="btn btn-primary"
            onClick={submitHandle}
          >
            Go!
          </button>
        </div>
        <div className="navbar-end"></div>
      </div>

      <div className='bg-base-300 p-4 w-4/5 rounded-box m-auto content-center grid' style={{ height: "600px" }}>
        <div className="flex justify-evenly items-center w-full m-auto" >
          <div className="justify-center content-center grid" style={{ flexBasis: "40%", height: "400px" }}>
            {imgURL == '' ? (<div className='flex items-center text-3xl'>Image Preview</div>) :
              (<img src={imgURL} alt='Image Preview' style={{ width: "auto", maxHeight: "400px" }}></img>)}
          </div>
          <div className="" style={{ flexBasis: "40%" }}>
            {loading ? (
              <div className="bouncing-loader">
                <div></div>
                <div></div>
                <div></div>
              </div>) : (
              <div className="overflow-x-auto">
                <table className="table w-full rounded-lg">



                  <tbody className="">

                    <tr>
                      <th >
                        Tags
                      </th>
                      <td className="px-3 py-4 whitespace-normal">
                        <p className="break-all">
                          {data['ImageTagging']}
                        </p>
                      </td>

                    </tr>

                    <tr>
                      <th>
                        Description
                      </th>
                      <td className="px-3 py-4 whitespace-normal">{data['ImageDescription']}</td>

                    </tr>

                    <tr>

                      <th>
                        OCR
                      </th>
                      <td className="px-3 py-4 whitespace-normal">{data['OCR']}</td>
                    </tr>
                    <tr>

                      <th>
                        Custom
                      </th>
                      <td className="px-3 py-4 whitespace-normal">{data['Custom']}</td>
                    </tr>
                  </tbody>

                </table>
              </div>)}
          </div>
        </div>
      </div>
      <Gallery
        images={images}
        enableImageSelection={false}
        rowHeight={320}
      // tileViewportStyle={styleSmall}
      />
    </div>
  )
}

export default App
